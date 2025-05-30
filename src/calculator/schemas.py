from typing import List, Literal, Optional
from datetime import datetime

from pydantic import BaseModel

class DeliveryLocation(BaseModel):
    code: int

class DeliveryPackage(BaseModel):
    weight: int
    length: int
    width: int
    height: int    

class DeliveryRequest(BaseModel):
    service: Literal['cdek']
    from_location: DeliveryLocation
    to_location: DeliveryLocation
    packages: List[DeliveryPackage]
    date: Optional[datetime] = None
    delivery_type: Optional[int] = 1
    currency: Optional[int] = 1
    lang: Optional[str] = 'rus'

class DeliveryResponse(BaseModel):
    delivery_sum: float
    period_min: int
    period_max: int
    service_name: str = 'СДЭК'
