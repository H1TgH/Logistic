from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import Annotated


app = FastAPI()

DATABASE_URL = "postgresql+asyncpg://Logistic:Logistic@localhost/Logistic"
engine = create_async_engine(DATABASE_URL, echo=True)

new_async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with new_async_session() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]