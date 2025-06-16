from datetime import datetime

from sqlalchemy import select

from fastapi import HTTPException, status, APIRouter

from src.users.schemas import UserRegistrationSchema
from src.database import SessionDep
from src.users.models import UserModel
from src.users.utils import hashing_password, generate_api_key
from src.logger import setup_logger


logger = setup_logger('users.register')
register_router = APIRouter()

@register_router.post('/api/v1/public/register', tags=['auth'])
async def register(user_data: UserRegistrationSchema, session: SessionDep):
    logger.info(f"Попытка регистрации пользователя: {user_data.username} с email: {user_data.email}")
    
    is_user_exist = await session.execute(
        select(UserModel).
        where(
            (UserModel.email == user_data.email) |
            (UserModel.username == user_data.username)
        )
    )

    if is_user_exist.scalar():
        logger.warning(f"Ошибка регистрации - пользователь уже существует: {user_data.username}")
        raise HTTPException (
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Пользователь с таким адресом электронной почты или логином уже существует.'
        )

    if user_data.password != user_data.password_confirm:
        logger.warning(f"Ошибка регистрации - пароли не совпадают для пользователя: {user_data.username}")
        raise HTTPException (
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Пароли не совпадают!'
        )

    new_user = UserModel(
        email = user_data.email,
        username = user_data.username,
        phone = user_data.phone,
        password = hashing_password(user_data.password),
        api_key = generate_api_key(),
        created_at = datetime.now(),
        updated_at = datetime.now()
    )

    session.add(new_user)
    await session.commit()
    logger.info(f"Успешная регистрация нового пользователя: {user_data.username}")

    return {'message': 'Пользователь успешно зарегистрирован.'}