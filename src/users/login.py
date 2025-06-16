from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from src.database import SessionDep
from src.users.schemas import UserLoginSchema
from src.users.utils import pwd_context, generate_api_key
from src.users.models import UserModel
from src.logger import setup_logger


logger = setup_logger('users.login')
login_router = APIRouter()

@login_router.post('/api/v1/public/login', tags=['auth'])
async def login(session: SessionDep, user_data: UserLoginSchema):
    logger.info(f"Попытка входа пользователя: {user_data.login}")
    user = await session.scalar(
        select(UserModel).where(
            (UserModel.email == user_data.login) |
            (UserModel.username == user_data.login)
        )
    )

    if not user or not pwd_context.verify(user_data.password, user.password):
        logger.warning(f"Неудачная попытка входа для пользователя: {user_data.login}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Неверные учетные данные'
        )
    
    if not user.api_key:
        logger.info(f"Генерация нового API ключа для пользователя: {user.username}")
        user.api_key = generate_api_key()
        await session.commit()
    
    logger.info(f"Успешный вход пользователя: {user.username}")
    return {
        'access_token': user.api_key,
        'token_type': 'token',
        'username': user.username
    }