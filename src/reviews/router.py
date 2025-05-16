from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status

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

    if user_review.parent_id:
        parent_review = await sesion.get(ReviewModel, user_review.parent_id)
        if not parent_review:
            raise HTTPException(status_code=404, detail="Родительский отзыв не найден")
        if parent_review.parent_id is not None:
            raise HTTPException(status_code=400, detail="Нельзя ответить на ответ")

    new_review = ReviewModel(
        user_id=current_user.id,
        review=user_review.review,
        rate=user_review.rate,
        created_at=date.today(),
        parent_id=user_review.parent_id
    )

    sesion.add(new_review)
    await sesion.commit()
    return {'message': 'Отзыв успешно оставлен.'}
