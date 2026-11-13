from fastapi import APIRouter, Depends, HTTPException, status
from app.api.v1.tags.repository import TagRepository
from app.api.v1.tags.schemas import TagCreate, TagPublic
from app.core.db import get_connection_db
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.security import get_current_user


router = APIRouter(prefix="/tags", tags=["tags"])


@router.post("", response_model=TagPublic,
             response_description="Post Created Ok",
             status_code=status.HTTP_201_CREATED
             )
def create_tags(tag: TagCreate,
                db: Session = Depends(get_connection_db),
                user=Depends(get_current_user)):
    repository = TagRepository(db)
    try:
        tag_created = repository.create_tag(tag_name=tag.tag_name)
        db.commit()
        db.refresh(tag_created)
        return tag_created
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error Creating tag"
        )
