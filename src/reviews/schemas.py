from pydantic import BaseModel


class ReviewCreateSchema(BaseModel):
    review: str
    rate: int

