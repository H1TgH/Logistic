from typing import List, Literal, Optional
from datetime import datetime
from pydantic import BaseModel


class DeliveryLocation(BaseModel):
    city_name: str

class DeliveryPackage(BaseModel):
    weight: int
    length: int
    width: int
    height: int    

class DeliveryRequest(BaseModel):
    service: Literal['cdek', 'pecom', 'all']
    from_location: DeliveryLocation
    to_location: DeliveryLocation
    packages: List[DeliveryPackage]
    date: Optional[datetime] = None
    delivery_type: Optional[int] = 1
    currency: Optional[int] = 1
    lang: Optional[str] = 'rus'

class DeliveryResult(BaseModel):
    service_name: str
    delivery_sum: int
    period_min: int
    period_max: int
    service_url: str
    service_logo: str

class DeliveryResponse(BaseModel):
    from_location: DeliveryLocation  
    to_location: DeliveryLocation
    packages: List[DeliveryPackage]
    delivery_type: Optional[int] = 1
    shipment_date: Optional[datetime] = None  
    results: List[DeliveryResult]