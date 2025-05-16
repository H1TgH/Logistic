from datetime import date
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, String, SmallInteger, ForeignKey

from src.database import Base


class ReviewModel(Base):
    __tablename__ = 'reviews'

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        nullable=False
    )
    
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id'),
        nullable=False
    )

    review: Mapped[str] = mapped_column(
        String(1000),
        nullable=True,
    )

    rate: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False
    )

    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('reviews.id'), nullable=True
    )

    created_at: Mapped[date] = mapped_column(
        nullable=False
    )