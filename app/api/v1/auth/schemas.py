from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

Role = Literal["user", "editor", "admin"]


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class UserPublic(UserBase):
    id: int
    role: Role
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=7, max_length=20)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class RoleUpdate(BaseModel):
    role: Role


class TokenData(BaseModel):
    sub: str
    username: str
