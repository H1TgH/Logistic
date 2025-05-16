from datetime import datetime

from sqlalchemy import select

from fastapi import HTTPException, status, APIRouter

from src.users.schemas import UserRegistrationSchema
from src.database import SessionDep
from src.users.models import UserModel
from src.users.utils import hashing_password, generate_api_key


register_router = APIRouter()

@register_router.post('/api/register', tags=['auth'])
async def register(user_data: UserRegistrationSchema, session: SessionDep):
    is_user_exist = await session.execute(
        select(UserModel).
        where(
            (UserModel.email == user_data.email) |
            (UserModel.username == user_data.username)
        )
    )

    if is_user_exist.scalar():
        raise HTTPException (
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Пользователь с таким адресом электронной почты или логином уже существует.'
        )

    if user_data.password != user_data.password_confirm:
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

    return {'message': 'Пользователь успешно зарегистрирован.'}