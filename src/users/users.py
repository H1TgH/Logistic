from fastapi import APIRouter, Depends, HTTPException, status

from src.users.utils import get_current_user
from src.users.models import UserModel
from src.users.schemas import UpdatePhoneNumberSchema, UpdateNameSchema, UpdateSurnameSchema
from src.database import SessionDep


users_router = APIRouter()

@users_router.patch('/api/users/me/phone')
async def editing_phone(
    session: SessionDep,
    request: UpdatePhoneNumberSchema,
    current_user: UserModel = Depends(get_current_user),
):
    current_user.phone = request.phone
    await session.commit()

    return {'message': 'Номер телефона успешно изменен.'}

users_router = APIRouter()

@users_router.patch('/api/users/me/name')
async def editing_name(
    session: SessionDep,
    request: UpdateNameSchema,
    current_user: UserModel = Depends(get_current_user),
):
    current_user.name = request.name
    await session.commit()

    return {'message': 'Имя пользователя успешно изменено.'}

@users_router.patch('/api/users/me/surname')
async def editing_surname(
    session: SessionDep,
    request: UpdateSurnameSchema,
    current_user: UserModel = Depends(get_current_user),
):
    current_user.surname = request.surname
    await session.commit()

    return {'message': 'Фамилия пользователя успешно изменена.'}