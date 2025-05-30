from fastapi import APIRouter, Depends, HTTPException
from src.database import SessionDep
from src.calculator.schemas import DeliveryRequest, DeliveryResponse
from src.cdek.utils import calculate_cdek_delivery

calculator_router = APIRouter(tags=['calculator'])

@calculator_router.post('/api/v1/public/calculate', response_model=DeliveryResponse)
async def calculate_delivery(
    request: DeliveryRequest,
    session: SessionDep,
):
    if request.service == 'cdek':
        try:
            result = await calculate_cdek_delivery(
                session=session,
                from_location_code=request.from_location.code,
                to_location_code=request.to_location.code,
                packages=request.packages,
                date=request.date,
                currency=request.currency,
                lang=request.lang,
                delivery_type=request.delivery_type,
            )
            return result
        except Exception as e:
            raise HTTPException(status_code=502, detail=f'CDEK API error: {str(e)}')
    else:
        raise HTTPException(status_code=400, detail='Unknown delivery service')
