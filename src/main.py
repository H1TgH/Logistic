from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.users.router import main_router
from src.reviews.router import review_router
from src.calculator.router import calculator_router


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(main_router)
app.include_router(review_router)
app.include_router(calculator_router)