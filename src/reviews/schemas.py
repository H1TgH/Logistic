from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class ReviewCreateSchema(BaseModel):
    review: str
    rate: Optional[int] = Field(None, ge=1, le=5)
    parent_id: Optional[int] = None

class ReviewResponseSchema(BaseModel):
    id: int
    user_id: int
    username: str
    review: Optional[str]
    rate: Optional[int]
    created_at: date
    parent_id: Optional[int]


class ReviewWithRepliesSchema(ReviewResponseSchema):
    replies: List[ReviewResponseSchema] = []