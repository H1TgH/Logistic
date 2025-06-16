from fastapi import APIRouter, Depends, HTTPException, status

from src.users.utils import get_current_user, hashing_password, pwd_context
from src.users.models import UserModel
from src.users.schemas import UpdatePhoneNumberSchema, UpdateNameSchema, UpdateSurnameSchema, UpdatePasswordSchema
from src.database import SessionDep
from src.logger import setup_logger


logger = setup_logger('users')
users_router = APIRouter()

@users_router.patch('/api/v1/users/me/phone', tags=['users_edit'])
async def editing_phone(
    session: SessionDep,
    request: UpdatePhoneNumberSchema,
    current_user: UserModel = Depends(get_current_user),
):
    logger.info(f"Пользователь {current_user.username} изменяет номер телефона")
    current_user.phone = request.phone
    await session.commit()
    logger.info(f"Номер телефона успешно изменен для пользователя {current_user.username}")
    return {'message': 'Номер телефона успешно изменен.'}

@users_router.patch('/api/v1/users/me/name', tags=['users_edit'])
async def editing_name(
    session: SessionDep,
    request: UpdateNameSchema,
    current_user: UserModel = Depends(get_current_user),
):
    logger.info(f"Пользователь {current_user.username} изменяет имя")
    current_user.name = request.name
    await session.commit()
    logger.info(f"Имя успешно изменено для пользователя {current_user.username}")
    return {'message': 'Имя пользователя успешно изменено.'}

@users_router.patch('/api/v1/users/me/surname', tags=['users_edit'])
async def editing_surname(
    session: SessionDep,
    request: UpdateSurnameSchema,
    current_user: UserModel = Depends(get_current_user),
):
    logger.info(f"Пользователь {current_user.username} изменяет фамилию")
    current_user.surname = request.surname
    await session.commit()
    logger.info(f"Фамилия успешно изменена для пользователя {current_user.username}")
    return {'message': 'Фамилия пользователя успешно изменена.'}

@users_router.patch('/api/v1/users/me/password', tags=['users_edit'])
async def editing_password(
    session: SessionDep,
    request: UpdatePasswordSchema,
    current_user: UserModel = Depends(get_current_user)
):
    logger.info(f"Пользователь {current_user.username} пытается изменить пароль")
    if not pwd_context.verify(request.old_password, current_user.password):
        logger.warning(f"Неверный текущий пароль для пользователя {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Введен неверный текущий пароль.'
        )

    if pwd_context.verify(request.new_password, current_user.password):
        logger.warning(f"Новый пароль совпадает со старым для пользователя {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Пароли должны отличаться.'
        )
    
    new_password = hashing_password(request.new_password)
    current_user.password = new_password
    await session.commit()
    logger.info(f"Пароль успешно изменен для пользователя {current_user.username}")
    return {'message': 'Пароль успешно изменен.'}
