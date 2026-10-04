import math
from datetime import datetime
from fastapi import FastAPI, Query, HTTPException, Path, status, Depends
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
from typing import Optional, List, Union, Literal
from sqlalchemy import create_engine, Integer, String, DateTime, Text, select, func, UniqueConstraint, ForeignKey, Table, Column# NOQA
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase, Mapped, mapped_column, relationship, selectinload, joinedload # NOQA
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from core.db import Base


class AuthorORM(Base):
    __tablename__ = "authors"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    posts: Mapped[List["PostORM"]] = relationship(back_populates="author")


post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id", ondelete="CASCADE"),
           primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"),
           primary_key=True)
)


class TagsORM(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tag_name: Mapped[str] = mapped_column(String(30),
                                          unique=True, nullable=False)
    posts: Mapped[List["PostORM"]] = relationship(
        secondary=post_tags,
        back_populates="tags",
        lazy="selectin"
    )


class PostORM(Base):
    __tablename__ = "posts"
    __table_args__ = ((UniqueConstraint("title", name="unique_post_title")),)
    id: Mapped[int] = mapped_column(Integer,
                                    primary_key=True,
                                    index=True)
    title: Mapped[str] = mapped_column(String(100),
                                       nullable=False,
                                       index=True)
    content: Mapped[str] = mapped_column(Text,
                                         nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime,
                                                 default=datetime.utcnow)
    author_id: Mapped[Optional[int]] = mapped_column(ForeignKey("authors.id"))
    author: Mapped[Optional["AuthorORM"]] = relationship(
        back_populates="posts"
    )
    tags: Mapped[List["TagsORM"]] = relationship(
        secondary=post_tags,
        back_populates="posts",
        lazy="selectin",
        passive_deletes=True
    )


Base.metadata.create_all(bind=engine)  # DEV enviroment

app = FastAPI(title='Mini Blog')
banned_words = ["puta", "porno", "pipi", "cuca", "spam"]


class Author(BaseModel):
    name: str = Field(
        ...,
        min_length=4,
        max_length=20,
        description="Nombre del Autor"
    )
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


class Tag(BaseModel):
    tag_name: str = Field(
        ...,
        min_length=2,
        max_length=30,
        description="Nombre de la etiqueta"
    )
    model_config = ConfigDict(from_attributes=True)


class PostBase(BaseModel):
    title: str
    content: str
    tags: Optional[List[Tag]] = Field(default_factory=list) # Create list for every object # NOQA
    author: Optional[Author] = None


class PostCreate(BaseModel):
    title: str = Field(
        ...,
        min_length=5,
        max_length=100,
        description='Titulo del post (min 5 max 100)',
        examples=["Mi primer Post con FastAPI"]
    )
    content: Optional[str] = Field(
        min_length=10,
        max_length=200,
        default="Default de un Post",
        description="Contenido del Post no mames wey",
        examples=["Descripcion de un post mano todo bn sisa"]
    )
    tags: List[Tag] = Field(default_factory=list)
    author: Author = None

    @field_validator("title")
    @classmethod
    def not_allowed_title(cls, value: str) -> str:
        for palabra in banned_words:
            if palabra.lower() in value.lower():
                raise ValueError(f"Titulo no valido, borra \'{palabra}\'"
                                 " porfavor")
        return value


class postUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    content: Optional[str] = None


class PostPublic(PostBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class PostSummary(BaseModel):
    id: int
    title: str
    model_config = ConfigDict(from_attributes=True)


class PaginatedPost(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int
    has_prev: bool
    has_next: bool
    order_by: Literal["id", "title"]
    direction: Literal["asc", "desc"]
    search: Optional[str] = None
    items: List[PostPublic]


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
    results = select(PostORM)

    if query:
        results = results.where(PostORM.title.ilike(f"%{query}%"))

    total = db.scalar(select(func.count()).select_from(results.subquery())) or 0  # noqa

    #results = sorted(results, key=lambda post: post[order_by], reverse= direction=="desc") # noqa

    total_pages = math.ceil(total / limit) if total > 0 else 0

    if order_by == "id":
        order_col = PostORM.id
    else:
        order_col = func.lower(PostORM.title)

    results = results.order_by(
        order_col.asc() if direction == "asc" else order_col.desc()
    )
    if total_pages > 0:
        items = db.execute(results.limit(limit).offset(offset)).scalars().all()
    else:
        items = []
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
    normalized_tags_name = [tag.strip().lower() for tag in tags if tag.strip()]
    print(normalized_tags_name)
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

    posts = db.execute(post_list).scalars().all()
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
