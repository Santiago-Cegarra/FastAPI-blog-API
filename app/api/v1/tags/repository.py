from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.api.v1.tags.schemas import TagPublic
from app.models.tags import TagsORM
from app.services.pagination import paginated_query


class TagRepository:
    def __init__(self, db: Session):
        self.db = db

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
