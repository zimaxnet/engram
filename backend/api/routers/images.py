from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import logging

from backend.core import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/{filename}")
async def get_image(filename: str):
    print(f"DEBUG: get_image called with {filename}")
    """
    Serve an image from the docs/images directory.
    """
    try:
        settings = get_settings()
        docs_path = Path(settings.onedrive_docs_path or "docs")
        images_dir = docs_path / "images"
        
        # Sanitize filename (basic check)
        if ".." in filename or "/" in filename:
             raise HTTPException(status_code=400, detail="Invalid filename")
             
        file_path = images_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")
            
        return FileResponse(file_path)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving image {filename}: {e}")
        raise HTTPException(status_code=500, detail="Error serving image")
