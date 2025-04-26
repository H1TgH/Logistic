from fastapi import APIRouter, HTTPException, status

from sqlalchemy import select

from src.users.dependencies import SessionDep
from src.users.schemas import UserLoginSchema
from src.users.utils import pwd_context, generate_api_key
from src.users.models import UserModel


login_router = APIRouter()

@login_router.post("/login")
async def login(session: SessionDep, user_data: UserLoginSchema):
    user = await session.scalar(
        select(UserModel).where(
            (UserModel.email == user_data.login) |
            (UserModel.username == user_data.login)
        )
    )

    if not user or not pwd_context.verify(user_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные"
        )
    
    if not user.api_key:
        user.api_key = generate_api_key()
        await session.commit()
    
    return {
        "access_token": user.api_key,
        "token_type": "token"
    }