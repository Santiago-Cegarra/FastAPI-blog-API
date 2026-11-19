from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.v1.tags.repository import TagRepository
from app.api.v1.tags.schemas import TagCreate, TagPublic
from app.core.db import get_connection_db
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.security import get_current_user


router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=dict)
def list_tags(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    order_by: str = Query("id", pattern="^(id|name)"),
    direction: str = Query("asc", pattern="^(asc|desc)$"),
    search: str | None = Query(None),
    db: Session = Depends(get_connection_db)
):
    repo = TagRepository(db)

    return repo.list_tags(
        page=page,
        limit=per_page,
        order_by=order_by,
        direction=direction,
        search=search
    )


@router.post("", response_model=TagPublic,
             response_description="Post Created Ok",
             status_code=status.HTTP_201_CREATED
             )
def create_tags(
    tag: TagCreate,
    db: Session = Depends(get_connection_db),
    user=Depends(get_current_user)
):
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


@router.put("/{tag_id}",
            response_description="Post Updated Succesfully",
            status_code=status.HTTP_200_OK
            )
def update_tag(
    tag_id: int,
    db: Session = Depends(get_connection_db),
    name: str | None = None,
    user=Depends(get_current_user)
):
    repository = TagRepository(db)
    tag = repository.update_tag(id=tag_id, name=name)
    if tag is None:
        raise HTTPException(
            status_code=404,
            detail="Tag not found"
        )
    db.commit()
    return {
        "tag": tag.tag_name
    }


@router.delete("/{tag_id}",
               response_description="Post Deleted",
               status_code=status.HTTP_204_NO_CONTENT
               )
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_connection_db),
    user=Depends(get_current_user)
):
    repository = TagRepository(db)
    tag_exists = repository.delete_tag(tag_id)
    if not tag_exists:
        raise HTTPException(
            status_code=404,
            detail="Tag not found"
        )

    db.commit()
    return None


@router.get("/popular_tag")
def most_popular_tag(
    db: Session = Depends(get_connection_db),
    user=Depends(get_current_user)
):
    repository = TagRepository(db)
    result = repository.most_popular_tag()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Not Tag to show"
        )

    return result
