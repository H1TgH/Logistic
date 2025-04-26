from passlib.context import CryptContext
from secrets import token_urlsafe

from sqlalchemy import select

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.users.models import UserModel
from src.users.dependencies import SessionDep


pwd_context = CryptContext(schemes=['bcrypt'], deprecated="auto")
security_scheme = HTTPBearer(bearerFormat="TOKEN")

def hashing_password(password: str) -> str:
    return pwd_context.hash(password)

def generate_api_key() -> str:
    return token_urlsafe(32)

async def get_current_user(session: SessionDep, credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> UserModel:
    token = credentials.credentials
    user = await session.scalar(
        select(UserModel).
        where(UserModel.api_key == token)
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен авторизации",
            headers={"WWW-Authenticate": "TOKEN"}
        )
    return user