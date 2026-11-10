import os
import shutil
import uuid
from fastapi import UploadFile, HTTPException, status


MEDIA_DIRECTORY = "app/media"
ALLOWED_MIME = ["image/png", "image/jpeg"]


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
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": filename,
        "content_type": file.content_type,
        "url": f"/media/{filename}"
    }
