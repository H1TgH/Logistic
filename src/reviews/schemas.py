from pydantic import BaseModel
from typing import Optional
from datetime import date

class ReviewCreateSchema(BaseModel):
    review: str
    rate: int
    parent_id: Optional[int] = None

class ReviewResponseSchema(BaseModel):
    id: int
    user_id: int
    review: Optional[str]
    rate: int
    created_at: date
    parent_id: Optional[int]
