from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from app.models import AuthorORM, PostORM, TagsORM


class PostRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, post_id: int) -> Optional[PostORM]:
        post_find = select(PostORM).where(PostORM.id == post_id)
        return self.db.execute(post_find).scalar_one_or_none()
