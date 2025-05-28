from pydantic import BaseModel


class CDEKCalculateRequest(BaseModel):
    tariff_code: int
    from_location: dict
    to_location: dict
    packages: list

class CDEKCalculateResponse(BaseModel):
    delivery_sum: float
    period_min: int
    period_max: int
    total_sum: float
    currency: str
