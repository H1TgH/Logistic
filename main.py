from fastapi import FastAPI, Depends, HTTPException, status

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, Date, Enum, func, select

from pydantic import BaseModel, EmailStr, field_validator

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


class UserRegistrationSchema(BaseModel):
    email: EmailStr
    username: str
    phone: str
    password: str
    password_confirm: str

    @field_validator('username')
    def validate_username(cls, username):
        if len(username) < 3:
            raise ValueError('Логин должен составлять хотя бы 3 символа.')
        if len(username) > 32:
            raise ValueError('Логин слишком длинный. Максимальная длина - 32.')
        return username
    
    @field_validator('phone')
    def validate_phone_number(cls, phone_number):
        if len(phone_number) < 12:
            raise ValueError('Номер телефона слишком короткий.')
        if len(phone_number) > 12:
            raise ValueError('Номер телефона слишком длинный.')
        return phone_number

    @field_validator('password')
    def validate_password(cls, password):
        if len(password) < 8:
            raise ValueError('Пароль слишком короткий. Минимальная длина пароля: 8.')
        return password


def hashing_password(password: str) -> str:
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated="auto")
    return pwd_context.hash(password)

@app.post('/register')
async def register(session: SessionDep, user_data: UserRegistrationSchema):
    is_user_exist = await session.execute(
        select(UserModel).where(
            (UserModel.email == user_data.email) |
            (UserModel.username == user_data.username)
        )
    )

    if is_user_exist.scalar():
        raise HTTPException (
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Пользователь с таким адресом электронной почты или логином уже существует.'
        )
    print(user_data.password, user_data.password_confirm)
    if user_data.password != user_data.password_confirm:
        print(user_data.password, user_data.password_confirm)
        raise HTTPException (
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Пароли не совпадают!'
        )

    new_user = UserModel(
        email = user_data.email,
        username = user_data.username,
        phone = user_data.phone,
        password = hashing_password(user_data.password),
        created_at = datetime.now(),
        updated_at = datetime.now()
    )

    session.add(new_user)
    await session.commit()

    return {'message': 'Пользователь успешно зарегистрирован.'}
