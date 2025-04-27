from fastapi import APIRouter, Depends, HTTPException, status

from src.users.utils import get_current_user
from src.users.models import UserModel
from src.users.schemas import UpdatePhoneNumberSchema
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