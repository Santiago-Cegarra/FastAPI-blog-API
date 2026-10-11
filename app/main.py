import math
from fastapi import FastAPI, Query, HTTPException, Path, status, Depends
from typing import Optional, List, Union, Literal
from sqlalchemy import create_engine, Integer, String, DateTime, Text, select, func, UniqueConstraint, ForeignKey, Table, Column# NOQA
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase, Mapped, mapped_column, relationship, selectinload, joinedload # NOQA
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from core.db import Base

Base.metadata.create_all(bind=engine)  # DEV enviroment

app = FastAPI(title='Mini Blog')


@app.get('/')
def home():
    return {'message': 'Welcome to the blog of Santiago'}


@app.get("/posts", response_model=PaginatedPost)
def list_posts(
    query: Optional[str] = Query(
        default=None,
        desc="Buscar por titulo",
        alias="search",
        min_length=3,
        max_length=20,
        pattern=r"^[a-zA-Z]+$",
    ),
    limit: int = Query(  # noqa
        10, ge=1, le=50, description="Resultados " "devueltos(1-50)" # noqa
    ),
    offset: int = Query(0, ge=0, description="Elementos desde"),  # noqa
    order_by: Literal["id", "title"] = Query("id", description="Order field"),  # noqa
    direction: Literal["asc", "desc"] = Query(  # noqa
        "asc", description="Direction Order"  # noqa
    ),
    db: Session = Depends(get_connection_db)
):
   
    return PaginatedPost(page=(offset // limit)+1,
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


@app.get('/posts/{id}', response_model=Union[PostPublic, PostSummary],
         response_description="Post Encontrado")
def get_post_by_id(id: int = Path(
    ...,
    gt=0,
    title="ID del post",
    description="ID entero del Post (no negativos)",
    examples=1
    ), include_content: bool | None = Query(default=True, desc="queryparam"),
    db: Session= Depends(get_connection_db)): # noqa
    post = db.get(PostORM, id)
    if not post:
        raise HTTPException(status_code=404, detail="Post no Encontrado")
    if include_content:
        return PostPublic.model_validate(post, from_attributes=True)

    return PostSummary.model_validate(post, from_attributes=True)


@app.get("/post/by-tags", response_model=List[PostPublic])
def filter_by_tags(
    tags: List[str] = Query(
        ...,
        min_length=1,
        description="One or more tags"
    ),
    db: Session = Depends(get_connection_db)
):
    # normalized_tags_name = [tag.strip().lower() for tag in tags if tag.strip()]
    # print(normalized_tags_name)
    # if not normalized_tags_name:
    #     return []
    # post_list = (
    #     select(PostORM).options(
    #         selectinload(PostORM.tags),
    #         joinedload(PostORM.author)
    #     ).where(PostORM.tags.any(
    #         func.lower(TagsORM.tag_name).in_(
    #             normalized_tags_name)
    #                 )
    #             ).order_by(PostORM.id.asc())
    # )

    # posts = db.execute(post_list).scalars().all()
    return posts


@app.post('/posts', response_model=PostPublic,
          response_description="Post Creado exitosamente",
          status_code=status.HTTP_201_CREATED,
          response_model_exclude_unset=True)
def create_post(post: PostCreate, db: Session = Depends(get_connection_db)):
    author_obj = None
    if post.author:
        author_obj = db.execute(
            select(AuthorORM).where(AuthorORM.email == post.author.email)
        ).scalar_one_or_none()
        if not author_obj:
            author_obj = AuthorORM(name=post.author.name,
                                   email=post.author.email)
            db.add(author_obj)
            db.flush()
    new_post = PostORM(title=post.title,
                       content=post.content,
                       author=author_obj)
    for tag in post.tags:
        tag_obj = db.execute(
            select(TagsORM).where(TagsORM.tag_name == tag.tag_name)
        ).scalar_one_or_none()
        if not tag_obj:
            tag_obj = TagsORM(tag_name=tag.tag_name)
            db.add(tag_obj)
            db.flush()
        new_post.tags.append(tag_obj)
    try:
        db.add(new_post)
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


@app.put('/posts/ {post_id}', response_model=PostPublic,
         response_description="Post Actualizado Correctamente",
         response_model_exclude_none=True)
def update_post_by_id(post_id: int, data: postUpdate,
                      db: Session = Depends(get_connection_db)):
    post = db.get(PostORM, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post no Encontrado")
    update = data.model_dump(exclude_unset=True)
    for k, v in update.items():
        setattr(post, k, v)
    db.commit()
    db.refresh(post)
    return PostPublic.model_validate(post, from_attributes=True)


@app.delete('/posts/{post_id}')
def delete_by_id(post_id: int,
                 db: Session = Depends(get_connection_db)):
    post = db.get(PostORM, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post no Encontrado")

    db.delete(post)
    db.commit()
    return {"status": "Post Borrado Exitosamente",
            "message": f"El post con ID: {post_id} '{post.title}' fue Eliminado"  # noqa
            }
