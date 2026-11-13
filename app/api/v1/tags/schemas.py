from pydantic import BaseModel, ConfigDict, Field


class TagPublic(BaseModel):
    id: int
    tag_name: str = Field(
        ...,
        min_length=2,
        max_length=30,
        description="Tag Name"
    )
    model_config = ConfigDict(from_attributes=True)


class TagCreate(BaseModel):
    tag_name: str = Field(
        ...,
        min_length=2,
        max_length=30,
        description="Tag Name"
    )


class TagUpdate(BaseModel):
    tag_name: str = Field(
        ...,
        min_length=2,
        max_length=30,
        description="Tag Name"
    )


class TagWithCount(BaseModel):
    id: int
    uses: int
    tag_name: str = Field(
        ...,
        min_length=2,
        max_length=30,
        description="Tag Name"
    )
    model_config = ConfigDict(from_attributes=True)
