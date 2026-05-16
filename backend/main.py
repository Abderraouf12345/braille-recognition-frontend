import io
import json
import numpy as np
import cv2
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import os
import re
import tempfile
import edge_tts

# Load environment variables from .env file
load_dotenv()

# Import the core modules
from core.model import load_model
from core.processor import BrailleProcessor

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

# Load model on startup
@app.on_event("startup")
async def startup_event():
    load_model()

@app.post("/process")
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
        # lightAngle is in degrees
        angle_rad = np.radians(lightAngle)
        V = np.array([np.cos(angle_rad), np.sin(angle_rad)])
        
        # Run heavy processing in background thread (returns braille, arabic, corrected)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            executor, 
            processor.process, 
            img, 
            pts_src, 
            V,
            language
        )
        
        # Unpack the three-part result
        if isinstance(result, tuple) and len(result) == 3:
            braille_text, arabic_text, gemini_text = result
        else:
            braille_text = str(result)
            arabic_text = ""
            gemini_text = ""
        
        return {
            "success": True,
            "braille": braille_text,
            "arabic": arabic_text,
            "gemini": gemini_text
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

class TTSRequest(BaseModel):
    text: str
    voice: str

@app.get("/voices")
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
        
        priority = ["Arabic", "French", "English", "Russian"]
        sorted_langs = [p for p in priority if p in data.keys()] + sorted([k for k in data.keys() if k not in priority])
        voice_data = {k: sorted(data[k], key=lambda x: x["label"]) for k in sorted_langs}
        return {"success": True, "voices": voice_data, "languages": sorted_langs}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/tts")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
