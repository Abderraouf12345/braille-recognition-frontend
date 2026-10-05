print(">>> [main] importing standard libs...", flush=True)
import io
import json
import numpy as np
import cv2
from fastapi import FastAPI, APIRouter, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse
from pydantic import BaseModel
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import os
import re
import tempfile
print(">>> [main] importing edge_tts...", flush=True)
import edge_tts
print(">>> [main] edge_tts OK", flush=True)

# Load environment variables from .env file
load_dotenv()

# Import the core modules
print(">>> [main] importing core.model...", flush=True)
from core.model import load_model
print(">>> [main] importing core.processor...", flush=True)
from core.processor import BrailleProcessor
print(">>> [main] all imports done", flush=True)

app = FastAPI(title="Braille Processing API")

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize thread pool for CPU heavy OpenCV and PyTorch tasks
executor = ThreadPoolExecutor(max_workers=4)

# Create processor instance
processor = BrailleProcessor()

# API router — importable by app.py for HF Spaces deployment
api_router = APIRouter()

# Load model on startup
@app.on_event("startup")
async def startup_event():
    try:
        print(">>> [startup] FastAPI startup event firing...", flush=True)
        load_model()
        print(">>> [startup] Model loaded successfully!", flush=True)
    except Exception as e:
        import traceback
        print(f">>> [startup] ERROR during model loading: {e}", flush=True)
        print(traceback.format_exc(), flush=True)


@api_router.get("/", response_class=HTMLResponse)
async def root():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Braille Recognition API</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a; color: #f8fafc;
            min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px;
        }
        .card {
            background: #1e293b; border: 1px solid #334155; border-radius: 16px;
            padding: 36px; max-width: 600px; width: 100%; box-shadow: 0 20px 40px rgba(0,0,0,0.5);
        }
        .header { display: flex; align-items: center; gap: 14px; margin-bottom: 20px; }
        .badge {
            background: #10b981; color: #022c22; font-size: 11px; font-weight: 700;
            padding: 4px 10px; border-radius: 20px; text-transform: uppercase; letter-spacing: 0.5px;
        }
        h1 { font-size: 24px; font-weight: 700; color: #f1f5f9; }
        p { color: #94a3b8; font-size: 14px; line-height: 1.6; margin-bottom: 24px; }
        .endpoints { list-style: none; display: flex; flex-direction: column; gap: 10px; }
        .endpoints li {
            background: #0f172a; border: 1px solid #334155; border-radius: 8px;
            padding: 10px 14px; font-family: monospace; font-size: 13px; display: flex; align-items: center; gap: 10px;
        }
        .method { font-weight: 700; padding: 2px 6px; border-radius: 4px; font-size: 11px; }
        .post { background: #3b82f6; color: white; }
        .get { background: #10b981; color: white; }
        .links { margin-top: 24px; display: flex; gap: 12px; }
        .links a {
            color: #38bdf8; text-decoration: none; font-size: 13px; font-weight: 600;
            padding: 8px 14px; background: rgba(56, 189, 248, 0.1); border-radius: 6px; border: 1px solid rgba(56, 189, 248, 0.2);
        }
        .links a:hover { background: rgba(56, 189, 248, 0.2); }
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h1>Braille Recognition API 🚀</h1>
            <span class="badge">Online</span>
        </div>
        <p>Headless FastAPI backend running on Hugging Face ZeroGPU. All endpoints are active and ready to receive requests.</p>
        <ul class="endpoints">
            <li><span class="method post">POST</span> <code>/process</code> — Process Braille image</li>
            <li><span class="method post">POST</span> <code>/process-stream</code> — Real-time progress SSE stream</li>
            <li><span class="method get">GET</span> <code>/voices</code> — Available TTS voices</li>
            <li><span class="method post">POST</span> <code>/tts</code> — Synthesize translated speech</li>
            <li><span class="method get">GET</span> <code>/health</code> — Health check</li>
        </ul>
        <div class="links">
            <a href="/docs" target="_blank">Swagger Docs &rarr;</a>
            <a href="/health" target="_blank">Health Check &rarr;</a>
        </div>
    </div>
</body>
</html>"""

@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}


@api_router.post("/process")
async def process_image(
    file: UploadFile = File(...),
    corners: str = Form(...),
    lightAngle: float = Form(...),
    language: str = Form("arabic")
):
    try:
        # Read the uploaded image into memory
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Parse corners (list of dicts [{x: ..., y: ...}, ...])
        pts_data = json.loads(corners)
        pts_list = [[pt['x'], pt['y']] for pt in pts_data]
        pts_src = np.float32(pts_list)
        
        # Compute V from light angle
        # lightAngle is in degrees, UI convention: 0° = top (12 o'clock), clockwise
        # In image space, Y-axis points downward, so we use:
        #   Vx = sin(angle)   (right at 90°)
        #   Vy = -cos(angle)  (up at 0° because Y is flipped)
        angle_rad = np.radians(lightAngle)
        V = np.array([np.sin(angle_rad), -np.cos(angle_rad)])
        
        # Run heavy processing in background thread (returns braille, translated)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            executor, 
            processor.process, 
            img, 
            pts_src, 
            V,
            language
        )
        
        # Unpack the two-part result
        if isinstance(result, tuple) and len(result) >= 2:
            braille_text, arabic_text = result[0], result[1]
        else:
            braille_text = str(result)
            arabic_text = ""
        
        return {
            "success": True,
            "braille": braille_text,
            "arabic": arabic_text
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.post("/process-stream")
async def process_image_stream(
    file: UploadFile = File(...),
    corners: str = Form(...),
    lightAngle: float = Form(...),
    language: str = Form("arabic")
):
    """
    Streaming endpoint using Server-Sent Events (SSE).
    Yields results progressively: braille → translation.
    """
    contents = await file.read()

    async def event_stream():
        try:
            nparr = np.frombuffer(contents, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            pts_data = json.loads(corners)
            pts_list = [[pt['x'], pt['y']] for pt in pts_data]
            pts_src = np.float32(pts_list)

            angle_rad = np.radians(lightAngle)
            V = np.array([np.sin(angle_rad), -np.cos(angle_rad)])

            # --- Run heavy image processing ---
            loop = asyncio.get_running_loop()
            braille_text, translated_text, overlay_image = await loop.run_in_executor(
                executor,
                processor.process,
                img, pts_src, V, language
            )

            # Yield overlay and braille immediately
            yield f"data: {json.dumps({'type': 'overlay', 'value': overlay_image})}\n\n"
            yield f"data: {json.dumps({'type': 'braille', 'value': braille_text})}\n\n"

            # Yield translation
            yield f"data: {json.dumps({'type': 'translation', 'value': translated_text})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'value': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


class TTSRequest(BaseModel):
    text: str
    voice: str

@api_router.get("/voices")
async def get_voices():
    try:
        manager = await edge_tts.VoicesManager.create()
        data = {}
        for v in manager.voices:
            full_info = v['FriendlyName'].split(" - ")[-1]
            base_lang = full_info.split("(")[0].strip() if "(" in full_info else full_info
            dialect = re.search(r'\((.*?)\)', full_info).group(1) if "(" in full_info else "Standard"
            p_name = v['ShortName'].split('-')[-1].replace('Neural','')
            gender = "M" if v['Gender'] == "Male" else "F"
            label = f"{dialect} — {p_name} ({gender})"
            if base_lang not in data: data[base_lang] = []
            data[base_lang].append({"label": label, "value": v['ShortName']})
        
        priority = ["Arabic", "French", "English", "Russian", "Chinese"]
        sorted_langs = [p for p in priority if p in data.keys()] + sorted([k for k in data.keys() if k not in priority])
        voice_data = {k: sorted(data[k], key=lambda x: x["label"]) for k in sorted_langs}
        return {"success": True, "voices": voice_data, "languages": sorted_langs}
    except Exception as e:
        return {"success": False, "error": str(e)}

@api_router.post("/tts")
async def generate_tts(request: TTSRequest):
    try:
        if not request.text.strip():
            return {"success": False, "error": "No text provided"}
            
        clean_text = request.text.replace('"', '').replace('\n', ' ')
        
        temp_dir = tempfile.gettempdir()
        output_file = os.path.join(temp_dir, f"speech_output_{hash(request.text)}.mp3")
        
        if os.path.exists(output_file):
            try: os.remove(output_file)
            except: pass
            
        communicate = edge_tts.Communicate(clean_text, request.voice)
        await communicate.save(output_file)
        
        if os.path.exists(output_file):
            return FileResponse(output_file, media_type="audio/mpeg", filename="speech.mp3")
        else:
            return {"success": False, "error": "Failed to generate audio file"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

# Include router in standalone app (for local development)
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
