from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.api.v1.tags.schemas import TagPublic
from app.models.post import PostORM, post_tags
from app.models.tags import TagsORM
from app.services.pagination import paginated_query


class TagRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_tag(self, id: int) -> Optional[TagsORM]:
        tag_find = select(TagsORM).where(TagsORM.id == id)
        return self.db.execute(tag_find).scalar_one_or_none()

    def create_tag(self, tag_name: str):

        tag_obj = self.db.execute(
            select(TagsORM).where(func.lower(TagsORM.tag_name == tag_name))
        ).scalar_one_or_none()
        if tag_obj:
            return tag_obj
        tag_obj = TagsORM(tag_name=tag_name)
        self.db.add(tag_obj)
        self.db.flush()
        return tag_obj

    def list_tags(
        self,
        search: Optional[str],
        order_by: str = "id",
        direction: str = "asc",
        page: int = 1,
        limit: int = 10
    ):
        query = select(TagsORM)
        if search:
            query = query.where(
                func.lower(
                    TagsORM.tag_name
                ).ilike(f"%{search.lower()}%")
            )

        allowed_order = {
            "id": TagsORM.id,
            "name": func.lower(TagsORM.tag_name)
        }

        result = paginated_query(
            db=self.db,
            model=TagsORM,
            base_query=query,
            page=page,
            per_page=limit,
            order_by=order_by,
            direction=direction,
            allowed_order=allowed_order
        )

        result["items"] = [TagPublic.model_validate(item)
                           for item in result["items"]]

        return result

    def update_tag(self, id: int, name: str) -> Optional[TagsORM]:
        tag = self.get_tag(id)
        if not tag:
            return None
        if name is not None:
            tag.tag_name = name.strip().lower()

        self.db.add(tag)
        self.db.flush()
        self.db.refresh(tag)
        return tag

    def delete_tag(self, id: int):
        tag = self.get_tag(id=id)
        if not tag:
            return None
        self.db.delete(tag)
        return True

    def most_popular_tag(self) -> dict | None:

        row = (
            self.db.execute(
                select(
                    TagsORM.id.label("id"),
                    TagsORM.tag_name.label("tag_name"),
                    func.count(PostORM.id).label("uses")
                ).join(post_tags, post_tags.c.tag_id == TagsORM.id)
                .join(PostORM, PostORM.id == post_tags.c.post_id)
                .group_by(TagsORM.id, TagsORM.tag_name)
                .order_by(func.count(PostORM.id).desc(),
                          func.lower(TagsORM.tag_name).asc())
                .limit(1)
            )
            .mappings()
            .first()
        )

        return dict(row) if row else None
