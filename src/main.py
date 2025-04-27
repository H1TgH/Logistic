from fastapi import FastAPI, APIRouter

from src.users.router import main_router
from src.reviews.review import review_router


app = FastAPI()
app.include_router(main_router)
app.include_router(review_router)