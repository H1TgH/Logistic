from fastapi import APIRouter

from src.users.register import register_router
from src.users.login import login_router
from src.users.users import users_router


main_router = APIRouter()

main_router.include_router(register_router)
main_router.include_router(login_router)
main_router.include_router(users_router)