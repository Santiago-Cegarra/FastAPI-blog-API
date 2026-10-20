import os
from fastapi.security import OAuth2PasswordBearer
from datetime import timedelta, timezone, datetime
from typing import Optional
import jwt


SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-prod")
ALGORITHM = os.getenv("ALGORITHM", "HS-256")
ACCES_TOKEN_EXPIRE_MINUTE = int(os.getenv("ACCES_EXPIRE_TIME",
                                          "30"))

oauth_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def create_token(data: dict,
                 expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(tz=timezone.utc) + (expires_delta or timedelta(
        minutes=ACCES_TOKEN_EXPIRE_MINUTE
    ))
    to_encode.update({"exp": expire})
    token = jwt.encode(payload=to_encode,
                       key=SECRET_KEY,
                       algorithm=ALGORITHM)

    return token


def decode_token():
    pass
