from fastapi import FastAPI, Depends

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, Date, Enum, func

from typing import Annotated
from datetime import datetime

from passlib.context import CryptContext

from enum import Enum as PyEnum


app = FastAPI()

DATABASE_URL = "postgresql+asyncpg://Logistic:Logistic@localhost:5432/Logistic"
engine = create_async_engine(DATABASE_URL, echo=True)

new_async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with new_async_session() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

class Base(DeclarativeBase):
    pass

class Role(PyEnum):
    USER = 'user'
    ADMIN = 'admin'

class UserModel(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(32),unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(12), nullable=False)
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.USER, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(nullable=False, onupdate=func.now())
