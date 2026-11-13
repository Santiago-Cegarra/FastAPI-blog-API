from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
from typing import Optional, List, Literal, Annotated
from fastapi import Form
banned_words = ["example", "example", "example", "example", "spam"]


class Author(BaseModel):
    name: str = Field(
        ...,
        min_length=4,
        max_length=20,
        description="Author name"
    )
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


class Tag(BaseModel):
    tag_name: str = Field(
        ...,
        min_length=2,
        max_length=30,
        description="Tag name"
    )
    model_config = ConfigDict(from_attributes=True)


class PostBase(BaseModel):
    title: str
    content: str
    tags: Optional[List[Tag]] = Field(default_factory=list) # Create list for every object # NOQA
    author: Optional[Author] = None
    image_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class PostCreate(BaseModel):
    title: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description='Post title (min 5 max 100)',
        examples=["My first Post with FastAPI"]
    )
    content: Optional[str] = Field(
        min_length=10,
        max_length=200,
        default="Default Post content",
        description="Post content",
        examples=["A description of a post"]
    )
    tags: List[Tag] = Field(default_factory=list)
    # author: Author = None

    @field_validator("title")
    @classmethod
    def not_allowed_title(cls, value: str) -> str:
        for word in banned_words:
            if word.lower() in value.lower():
                raise ValueError(f"Invalid title, please remove \'{word}\'")
        return value

    @classmethod
    def as_form(
        cls,
        title: Annotated[str, Form(min_length=3)],
        content: Annotated[str, Form(min_length=10)],
        tags: Annotated[Optional[List[str]], Form()] = None,
    ):
        raw_tags: List[str] = []
        if tags:
            for item in tags:
                split_items = [part.strip() for part in item.split(",")
                               if part.strip()]
                raw_tags.extend(split_items)

        unique_tags = list(dict.fromkeys(raw_tags))

        tag_objs = [Tag(tag_name=t) for t in unique_tags]

        return cls(
            title=title,
            content=content,
            tags=tag_objs
        )


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
