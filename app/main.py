from fastapi import FastAPI
from app.core.db import Base, engine
from app.api.v1.posts.router import router as post_router
from app.api.v1.auth.router import router as auth_router
from app.api.v1.uploads.router import router as upload_router
from fastapi.staticfiles import StaticFiles
import os

MEDIA_DIRECTORY = "app/media"


def create_app() -> FastAPI:
    app = FastAPI(title="My Blog")
    Base.metadata.create_all(bind=engine)  # DEV enviroment
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(post_router)
    app.include_router(upload_router)

    os.makedirs(MEDIA_DIRECTORY, exist_ok=True)
    app.mount("/media",
              StaticFiles(directory=MEDIA_DIRECTORY),
              name="media")
    return app


app = create_app()
