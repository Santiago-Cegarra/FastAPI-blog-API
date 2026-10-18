from fastapi import FastAPI
from app.core.db import Base, engine
from app.api.v1.posts.router import router as post_router


def create_app() -> FastAPI:
    app = FastAPI(title="My Blog")
    Base.metadata.create_all(bind=engine)  # DEV enviroment
    app.include_router(post_router)
    return app


app = create_app()
