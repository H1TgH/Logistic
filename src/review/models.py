from src.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, String, Enum, func

class ReviewModel(Base):
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