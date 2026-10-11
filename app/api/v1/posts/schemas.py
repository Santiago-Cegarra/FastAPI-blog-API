from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
from typing import Optional, List, Literal
banned_words = ["example", "example", "example", "example", "spam"]


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
