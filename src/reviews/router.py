from datetime import date
from typing import List
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.database import SessionDep
from src.reviews.schemas import ReviewCreateSchema, ReviewResponseSchema, ReviewWithRepliesSchema
from src.users.models import UserModel
from src.reviews.models import ReviewModel
from src.users.utils import get_current_user
from src.logger import setup_logger


logger = setup_logger('reviews')
review_router = APIRouter()

@review_router.post('/api/v1/public/reviews', tags=['reviews'])
async def create_review(
    sesion: SessionDep,
    user_review: ReviewCreateSchema,
    current_user: UserModel = Depends(get_current_user)
):
    logger.info(f"Создание нового отзыва пользователем {current_user.username}")
    is_reply = user_review.parent_id is not None

    if not is_reply:
        if user_review.rate is None or not (1 <= user_review.rate <= 5):
            logger.warning(f"Некорректная оценка от пользователя {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Рейтинг обязателен и должен быть от 1 до 5 для основного отзыва'
            )
    else:
        parent_review = await sesion.get(ReviewModel, user_review.parent_id)
        if not parent_review:
            logger.warning(f"Родительский отзыв {user_review.parent_id} не найден")
            raise HTTPException(status_code=404, detail='Родительский отзыв не найден')
        if parent_review.parent_id is not None:
            logger.warning(f"Попытка ответить на ответ от пользователя {current_user.username}")
            raise HTTPException(status_code=400, detail='Нельзя ответить на ответ')

    new_review = ReviewModel(
        user_id=current_user.id,
        review=user_review.review,
        rate=user_review.rate if user_review.rate else 0,
        created_at=date.today(),
        parent_id=user_review.parent_id
    )

    sesion.add(new_review)
    await sesion.commit()
    logger.info(f"Отзыв успешно создан пользователем {current_user.username}")
    return {'message': 'Отзыв или ответ успешно оставлен.'}

@review_router.get('/api/v1/public/reviews', response_model=List[ReviewWithRepliesSchema], tags=['reviews'])
async def get_reviews(
    sesion: SessionDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=100)
):
    logger.info(f"Получение отзывов с пропуском {skip} и лимитом {limit}")
    query_main = select(ReviewModel).where(ReviewModel.parent_id == None).offset(skip).limit(limit)
    result_main = await sesion.execute(query_main)
    main_reviews = result_main.scalars().all()

    main_ids = [review.id for review in main_reviews]
    if not main_ids:
        logger.info("Отзывы не найдены")
        return []

    query_replies = select(ReviewModel).where(ReviewModel.parent_id.in_(main_ids))
    result_replies = await sesion.execute(query_replies)
    all_replies = result_replies.scalars().all()

    user_ids = {r.user_id for r in main_reviews + all_replies}
    query_users = select(UserModel).where(UserModel.id.in_(user_ids))
    result_users = await sesion.execute(query_users)
    users = result_users.scalars().all()
    user_map = {u.id: u.username for u in users}

    reply_map = defaultdict(list)
    for reply in all_replies:
        if len(reply_map[reply.parent_id]) < 3:
            reply_map[reply.parent_id].append(reply)

    response = []
    for main in main_reviews:
        response.append(ReviewWithRepliesSchema(
            id=main.id,
            user_id=main.user_id,
            username=user_map.get(main.user_id, 'Неизвестно'),
            review=main.review,
            rate=main.rate,
            created_at=main.created_at,
            parent_id=main.parent_id,
            replies=[
                ReviewResponseSchema(
                    id=r.id,
                    user_id=r.user_id,
                    username=user_map.get(r.user_id, 'Неизвестно'),
                    review=r.review,
                    rate=r.rate,
                    created_at=r.created_at,
                    parent_id=r.parent_id
                ) for r in reply_map.get(main.id, [])
            ]
        ))

    logger.info(f"Успешно получено {len(response)} отзывов с ответами")
    return response

@review_router.get('/api/v1/reviews/', response_model=List[ReviewWithRepliesSchema], tags=['reviews'])
async def get_user_reviews(
    session: SessionDep,
    user = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(5, le=100)
):
    logger.info(f"Получение отзывов пользователя {user.id} с пропуском {skip} и лимитом {limit}")
    
    query_main = select(ReviewModel).where(
        ReviewModel.user_id == user.id,
        ReviewModel.parent_id == None
    ).offset(skip).limit(limit)
    
    result_main = await session.execute(query_main)
    main_reviews = result_main.scalars().all()

    if not main_reviews:
        logger.info(f"Отзывы пользователя {user.id} не найдены")
        return []

    main_ids = [review.id for review in main_reviews]

    query_replies = select(ReviewModel).where(ReviewModel.parent_id.in_(main_ids))
    result_replies = await session.execute(query_replies)
    all_replies = result_replies.scalars().all()

    user_ids = {r.user_id for r in main_reviews + all_replies}
    query_users = select(UserModel).where(UserModel.id.in_(user_ids))
    result_users = await session.execute(query_users)
    users = result_users.scalars().all()
    user_map = {u.id: u.username for u in users}

    reply_map = defaultdict(list)
    for reply in all_replies:
        if len(reply_map[reply.parent_id]) < 3:
            reply_map[reply.parent_id].append(reply)

    response = []
    for main in main_reviews:
        response.append(ReviewWithRepliesSchema(
            id=main.id,
            user_id=main.user_id,
            username=user_map.get(main.user_id, 'Неизвестно'),
            review=main.review,
            rate=main.rate,
            created_at=main.created_at,
            parent_id=main.parent_id,
            replies=[
                ReviewResponseSchema(
                    id=r.id,
                    user_id=r.user_id,
                    username=user_map.get(r.user_id, 'Неизвестно'),
                    review=r.review,
                    rate=r.rate,
                    created_at=r.created_at,
                    parent_id=r.parent_id
                ) for r in reply_map.get(main.id, [])
            ]
        ))

    logger.info(f"Успешно получено {len(response)} отзывов пользователя {user.id} с ответами")
    return response