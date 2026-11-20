import os


class settings():
    JWT_KEY: str = os.getenv("SECRET_KEY", "change-me-in-prod")
    JWT_ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCES_TOKEN_EXPIRE_MINUTE: int = int(
        os.getenv("ACCES_EXPIRE_TIME", "30")
    )
