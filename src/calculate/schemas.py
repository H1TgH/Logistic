from pydantic import BaseModel
from typing import Literal, Optional


class DeliveryLocation(BaseModel):
    code: int


class DeliveryPackage(BaseModel):
    weight: int
    length: int
    width: int
    height: int


class DeliveryRequest(BaseModel):
    service: Literal["cdek"]
    from_location: DeliveryLocation
    to_location: DeliveryLocation
    package: DeliveryPackage
    tariff_code: Optional[int] = 137
    currency: Optional[int] = 1
    lang: Optional[str] = 'rus'
    delivery_type: Optional[int] = 0
