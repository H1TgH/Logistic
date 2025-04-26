from fastapi import FastAPI, APIRouter

from src.users.router import main_router


app = FastAPI()
app.include_router(main_router)