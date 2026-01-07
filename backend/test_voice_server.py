
from fastapi import FastAPI
# from backend.api.routers import voice # Removed to bypass __init__

from backend.core.config import get_settings
import uvicorn
import os

# Load .env
from dotenv import load_dotenv
load_dotenv()

# Force unset CORS_ORIGINS to prevent Pydantic crash
if "CORS_ORIGINS" in os.environ:
    print(f"DEBUG: Found CORS_ORIGINS in env: {os.environ['CORS_ORIGINS']}")
    del os.environ["CORS_ORIGINS"]

app = FastAPI()

# Import directly to avoid triggering __init__ of routers package if possible
from backend.api.routers.voice import router as voice_router
app.include_router(voice_router, prefix="/api/v1/voice", tags=["voice"])

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8123)
