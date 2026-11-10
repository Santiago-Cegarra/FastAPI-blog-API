from fastapi import APIRouter, File, UploadFile
from app.services.file_storage import save_uploaded_file


router = APIRouter(prefix="/upload", tags=["uploads"])

MEDIA_DIRECTORY = "app/media"


@router.post("/save")
async def save_file(file: UploadFile = File(...)):
    saved = save_uploaded_file(file)

    return {
        "filename": saved["filename"],
        "content_type": saved["content_type"],
        "url": saved["url"]
    }
