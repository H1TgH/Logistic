from typing import List, Literal, Optional
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
    tariff_code: Optional[int] = 137
    currency: Optional[int] = 1
    lang: Optional[str] = 'rus'
    delivery_type: Optional[int] = 0
