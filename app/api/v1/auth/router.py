from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.db import get_connection_db
from app.models.users import User
from .schemas import Token, UserCreate, UserLogin, UserPublic
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import create_token, get_current_user, hash_password, verify_pass
from .repository import UserRepository


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic,
             status_code=status.HTTP_201_CREATED
             )
def register_user(
    payload: UserCreate,
    db: Session = Depends(get_connection_db)
):
    repository = UserRepository(db)
    if repository.get_by_email(payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = repository.create_user(
        email=payload.email,
        hash_pass=hash_password(payload.password),
        full_name=payload.full_name
    )

    return UserPublic.model_validate(user)


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: Session = Depends(get_connection_db)):
    repository = UserRepository(db)
    user = repository.get_by_email(payload.email)

    if not user or not verify_pass(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials"
        )
    token = create_token(sub=str(user.id))

    return Token(
        access_token=token,
        user=UserPublic.model_validate(user)
    )


@router.get("/me", response_model=UserPublic)
def read_me(current: User = Depends(get_current_user)):
    return UserPublic.model_validate(current)
