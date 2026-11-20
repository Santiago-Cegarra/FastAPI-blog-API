import jwt
from fastapi.security import OAuth2PasswordBearer
from datetime import timedelta, timezone, datetime
from typing import Literal, Optional
from fastapi import Depends, HTTPException, status
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, PyJWTError
from pwdlib import PasswordHash
from app.core.db import get_connection_db
from app.models.users import User
from .config import settings
from sqlalchemy.orm import Session


password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer"
        }
)


def raise_expired_token():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token Expired",
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )


def raise_forbidden():
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have the necessary permissions to access this resource", # noqa
    )


def create_token(sub: str, minutes: int | None) -> dict:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=minutes or settings.ACCES_TOKEN_EXPIRE_MINUTE
    )

    return jwt.encode({
        "sub": sub,
        "exp": expire},
        settings.JWT_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def decode_token(token: str) -> dict:
    payload = jwt.decode(
        jwt=token,
        key=settings.JWT_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )

    return payload


async def get_current_user(
        db: Session = Depends(get_connection_db),
        token: str = Depends(oauth2_scheme)
) -> User:

    try:
        payload = decode_token(token)
        sub: Optional[str] = payload.get("sub")
        username: Optional[str] = payload.get("username")
        if not sub or not username:
            raise credentials_exc
        user_id = int(sub)

    except ExpiredSignatureError:
        raise raise_expired_token

    except InvalidTokenError:
        raise credentials_exc

    except PyJWTError:
        raise credentials_exc

    user = db.get(User, user_id)

    if not user or not user.is_active:
        raise credentials_exc

    return user


def hash_password(passw: str) -> str:
    return password_hash.hash(passw)


def verify_pass(passw: str, hashed: str) -> bool:
    return password_hash.verify(passw, hashed)


def require_role(min_role: Literal["user", "editor", "admin"]):
    order = {
        "user": 0,
        "editor": 1,
        "admin": 2
    }

    def evaluation(user: User = Depends(get_current_user)) -> User:
        if order[user.role] < order[min_role]:
            raise raise_forbidden()
        return user

    return evaluation


require_user = require_role("user")
require_editor = require_role("editor")
require_admin = require_role("admin")
