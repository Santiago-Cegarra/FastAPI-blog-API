import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./blog.db")
# print(f"Conectado a {DATABASE_URL}")

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, echo=True, future=True,
                       **engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autoflush=False,
                            autocommit=False, class_=Session)


class Base(DeclarativeBase):
    pass


def get_connection_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
