import os
import sys

print(">>> [1] Starting app.py...", flush=True)

# ── ZeroGPU Compatibility ──────────────────────────────────────────────
# On HF Spaces ZeroGPU, spaces must be imported first and at least one
# @spaces.GPU function must be defined and called during startup.
try:
    import spaces
    print(">>> [2] spaces imported OK (Hugging Face ZeroGPU environment)", flush=True)
except ImportError:
    # Graceful fallback for local development where 'spaces' is not installed
    class spaces:
        @staticmethod
        def GPU(fn):
            return fn
    print(">>> [2] spaces not found (running in standard/local mode)", flush=True)

@spaces.GPU
def _zerogpu_probe():
    """Satisfies Hugging Face ZeroGPU startup validator."""
    return True

# Call the probe function during startup so ZeroGPU registers GPU readiness
try:
    _zerogpu_probe()
    print(">>> [3] ZeroGPU probe initialized OK", flush=True)
except Exception as e:
    print(f">>> [3] ZeroGPU probe note: {e}", flush=True)

from main import app, load_model
print(">>> [4] FastAPI app imported OK", flush=True)

if __name__ == "__main__":
    import uvicorn
    # Preload model weights into memory before serving requests
    load_model()
    port = int(os.environ.get("PORT", 7860))
    print(f">>> [5] Starting Uvicorn server on port {port}...", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=port)


