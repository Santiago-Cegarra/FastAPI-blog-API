import os
import shutil
import uuid
from fastapi import UploadFile, HTTPException, status


MEDIA_DIRECTORY = "app/media"
ALLOWED_MIME = ["image/png", "image/jpeg"]
MAX_SIZE = int(os.getenv("MAX_UPLOAD_MB", "4"))
CHUNKS = 1024 * 1024


def save_uploaded_file(file: UploadFile):
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG and PNG images are allowed"
        )

    ext = os.path.splitext(file.filename)[1]  # get file extension
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(MEDIA_DIRECTORY, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer,
            length=1024 * 1024
        )

    size = os.path.getsize(file_path)
    if size > MAX_SIZE * CHUNKS:
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File too large, maximum size is {MAX_SIZE} MB"
        )

    return {
        "filename": filename,
        "content_type": file.content_type,
        "url": f"/media/{filename}",
        # "size": size
    }
