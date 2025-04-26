from enum import Enum as PyEnum
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, String, Enum, func

from src.database import Base

class Role(PyEnum):
    USER = 'user'
    ADMIN = 'admin'

class UserModel(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(
        BigInteger, 
        primary_key=True, 
        autoincrement=True, 
        index=True, 
        nullable=False
    )
    email: Mapped[str] = mapped_column(
        unique=True, 
        nullable=False
    )
    username: Mapped[str] = mapped_column(
        String(32), 
        unique=True, 
        nullable=False
    )
    phone: Mapped[str] = mapped_column(
        String(20), 
        unique=True,
        nullable=False
    )
    password: Mapped[str] = mapped_column(
        String(128), 
        nullable=False
    )
    api_key: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=True
    )
    role: Mapped[Role] = mapped_column(
        Enum(Role), 
        default=Role.USER, 
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        onupdate=func.now()
    )