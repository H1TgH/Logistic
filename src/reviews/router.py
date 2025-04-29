from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import select

from src.database import SessionDep
from src.reviews.schemas import ReviewCreateSchema
from src.users.models import UserModel
from src.reviews.models import ReviewModel
from src.users.utils import get_current_user


review_router = APIRouter()

@review_router.post('/api/review')
async def create_review(
    sesion: SessionDep,
    user_review: ReviewCreateSchema,
    current_user: UserModel = Depends(get_current_user)
):
    if not (user_review.rate in range(1, 6)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Рейтинг должен быть от 1 до 5'
        )
    
    new_review = ReviewModel(
        user_id = current_user.id,
        review=user_review.review,
        rate = user_review.rate,
        created_at = date.today()
    )

    sesion.add(new_review)
    await sesion.commit()

    return {'messege': 'Отзыв успешно оставлен.'}