from fastapi import APIRouter, Depends
from typing import Optional, List, Union, Literal
from sqlalchemy.orm import Session
from app.core.db import get_connection_db
from .schemas import PostPublic, PaginatedPost, postUpdate, PostCreate, PostSummary # noqa
from .repository import PostRepository
from fastapi import Query, Path, status, HTTPException
from math import ceil
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


router = APIRouter(prefix="/posts", tags=["post"])


@router.get("", response_model=PaginatedPost)
def list_posts(
    query: Optional[str] = Query(
        default=None,
        desc="Buscar por titulo",
        alias="search",
        min_length=3,
        max_length=20,
        pattern=r"^[a-zA-Z]+$",
    ),
    limit: int = Query(
        10, ge=1, le=50, description="Resultados " "devueltos(1-50)" # noqa
    ),
    offset: int = Query(0, ge=0, description="Elementos desde"),  # noqa
    order_by: Literal["id", "title"] = Query("id", description="Order field"),  # noqa
    direction: Literal["asc", "desc"] = Query(
        "asc", description="Direction Order"  # noqa
    ),
    db: Session = Depends(get_connection_db)
):
    page = (offset // limit)+1
    repository = PostRepository(db)
    total, items = repository.search(query, order_by, direction,
                                     page, limit)
    total_pages = ceil(total/limit) if total > 0 else False
    return PaginatedPost(page=page,
                         per_page=limit,
                         total=total,
                         total_pages=total_pages,
                         has_prev=offset > 0 and total > 0,
                         has_next=(offset // limit)+1 < total_pages if
                         total_pages > 0 else False,
                         order_by=order_by,
                         direction=direction,
                         search=query,
                         items=items)


@router.get("/{post_id}", response_model=Union[PostPublic, PostSummary],
            response_description="Post Not Found")
def get_post_by_id(post_id: int = Path(

    ...,
    gt=0,
    title="ID del post",
    description="ID entero del Post (no negativos)",
    examples=1
    ), include_content: bool | None = Query(default=True,
                                            description="queryparam"),
    db: Session = Depends(get_connection_db)
     ):

    repository = PostRepository(db)
    post = repository.get_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post no Encontrado")
    if include_content:
        return PostPublic.model_validate(post, from_attributes=True)

    return PostSummary.model_validate(post, from_attributes=True)


@router.get("", response_model=List[PostPublic])
def filter_by_tags(
    tags: List[str] = Query(
        ...,
        min_length=1,
        description="One or more tags"
    ),
    db: Session = Depends(get_connection_db)
):
    repository = PostRepository(db)
    return repository.search_by_tags(tags)


@router.post("", response_model=PostPublic,
             response_description="Post Created Succesfully",
             status_code=status.HTTP_201_CREATED,
             response_model_exclude_unset=True)
def create_post(post: PostCreate, db: Session = Depends(get_connection_db)):
    repository = PostRepository(db)
    try:
        new_post = repository.create_post(title=post.title,
                                          content=post.content,
                                          author=(post.author.model_dump()
                                                  if post.author else None),
                                          tags=[tag.model_dump()
                                                for tag in post.tags]
                                          )
        db.commit()
        db.refresh(new_post)
        return new_post
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409,
                            detail="Post Title Already Exist")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500,
                            detail="Error al crear el post")


@router.put("{post_id}", response_model=PostPublic,
            response_description="Post Updated Succesfully",
            response_model_exclude_none=True)
def update_post_by_id(post_id: int, data: postUpdate,
                      db: Session = Depends(get_connection_db)):
    repository = PostRepository(db)
    post = repository.get_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post no Encontrado")
    try:
        updates = data.model_dump(exclude_unset=True)
        post = repository.update_post(post, updates)
        db.commit()
        db.refresh(post)
        return post
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Error Updating Post"
        )


@router.delete("/{post_id}")
def delete_by_id(post_id: int,
                 db: Session = Depends(get_connection_db)):
    repository = PostRepository(db)
    post = repository.get_by_id(post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post no Encontrado")

    try:
        repository.delete_post(post)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Error Deleting Post"
        )
    return None
