from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, TIMESTAMP, DateTime, func

from src.database import Base


class DeliveryAPICredentials(Base):
    __tablename__ = 'delivery_api_credentials'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False
    )

    service_name: Mapped[String] = mapped_column(
        String,
        unique=True,
        nullable=False
    )

    client_login: Mapped[Text] = mapped_column(
        Text,
        nullable=True
    )

    client_secret: Mapped[Text] = mapped_column(
        Text,
        nullable=True
    )

    token: Mapped[Text] = mapped_column(
        Text,
        nullable=True
    )

    expires_at = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now(), 
        onupdate=func.now()
    )

class DadataCache(Base):
    __tablename__ = "dadata_cache"

    id = mapped_column(
        Integer, 
        primary_key=True, 
        index=True
    )
    
    original_address = mapped_column(
        String, 
        unique=True, 
        index=True
    )

    cleaned_city = mapped_column(
        String
    )

    created_at = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    
    updated_at = mapped_column(
        DateTime(timezone=True), 
        onupdate=func.now()
    )