from math import ceil
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import select, func
from typing import Optional, List, Tuple
from app.models import AuthorORM, PostORM, TagsORM


class PostRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, post_id: int) -> Optional[PostORM]:
        post_find = select(PostORM).where(PostORM.id == post_id)
        return self.db.execute(post_find).scalar_one_or_none()

    def search(self, query: Optional[str], order_by: str,
               direction: str, page: int, limit: int
               ) -> Tuple[int, List[PostORM]]:
        results = select(PostORM)
        if query:
            results = results.where(PostORM.title.ilike(f"%{query}%"))

        total = self.db.scalar(select(func.count()).select_from(results.subquery())) or 0 # noqa
        if total == 0:
            return 0, []

        current_page = min(page, max(1, ceil(total/limit)))
        order_col = PostORM.id if order_by == "id" else func.lower(
            PostORM.title)

        results = results.order_by(
                order_col.asc() if direction == "asc" else order_col.desc()
            )
        start = (current_page - 1) * limit
        items = self.db.execute(results.limit(
            limit).offset(start)).scalars().all()

        return total, items

    def search_by_tags(self, tags: List[str]) -> List[TagsORM]:
        normalized_tags_name = [tag.strip().lower() for tag in tags if tag.strip()] # noqa
        if not normalized_tags_name:
            return []
        post_list = (
            select(PostORM).options(
                selectinload(PostORM.tags),
                joinedload(PostORM.author)
            ).where(PostORM.tags.any(
                func.lower(TagsORM.tag_name).in_(
                    normalized_tags_name)
                        )
                    ).order_by(PostORM.id.asc())
        )

        return self.db.execute(post_list).scalars().all()

    def ensure_author(self, name: str, email: str) -> AuthorORM:
        author_obj = self.db.execute(
                select(AuthorORM).where(AuthorORM.email == email)
            ).scalar_one_or_none()
        if author_obj:
            return author_obj
        author_obj = AuthorORM(name=name,
                               email=email)
        self.db.add(author_obj)
        self.db.flush()
        return author_obj

    def ensure_tags(self, name: str) -> TagsORM:
        tag_obj = self.db.execute(
            select(TagsORM).where(TagsORM.ilike(name))
        ).scalar_one_or_none()
        if tag_obj:
            return tag_obj
        tag_obj = TagsORM(tag_name=name)
        self.db.add(tag_obj)
        self.db.flush()
        return tag_obj

    def create_post(self, title: str, content: str,
                    author: Optional[dict], tags: List[dict]) -> PostORM:
        author_obj = None
        if author:
            self.ensure_author(author['name'],
                               author['email'])
        post = PostORM(title=title, content=content, author=author_obj)
        for tag in tags:
            tag_obj = self.ensure_tags(tag["name"])
            post.tags.append(tag_obj)
        self.db.add(post)
        self.db.flush()
        self.db.refresh(post)
        return post

    def update_post(self, post, updates):
        for k, v in updates.items():
            setattr(post, k, v)
        self.db.flush()
        return post

    def delete_post(self, post) -> PostORM:
        self.db.delete(post)
        self.db.flush()
        return post
