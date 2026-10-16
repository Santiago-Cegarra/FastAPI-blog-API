import math
from fastapi import FastAPI, Query, HTTPException, Path, status, Depends
from typing import Optional, List, Union, Literal
from sqlalchemy import create_engine, Integer, String, DateTime, Text, select, func, UniqueConstraint, ForeignKey, Table, Column# NOQA
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase, Mapped, mapped_column, relationship, selectinload, joinedload # NOQA
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from core.db import Base

Base.metadata.create_all(bind=engine)  # DEV enviroment
app = FastAPI(title='Mini Blog')


@app.get('/')
def home():
    return {'message': 'Welcome to the blog of Santiago'}
