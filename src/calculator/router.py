from fastapi import APIRouter, Depends, HTTPException
from src.database import SessionDep
from src.calculator.schemas import DeliveryRequest, DeliveryResponse
from src.cdek.utils import calculate_cdek_delivery, get_city_code_by_name

calculator_router = APIRouter(tags=['calculator'])

@calculator_router.post('/api/v1/public/calculate', response_model=DeliveryResponse)
async def calculate_delivery(
    request: DeliveryRequest,
    session: SessionDep,
):
    if request.service == 'cdek':
        try:
            from_code = await get_city_code_by_name(session, request.from_location.city_name)
            to_code = await get_city_code_by_name(session, request.to_location.city_name)

            if from_code is None or to_code is None:
                raise HTTPException(status_code=400, detail='Не удалось определить код города')

            result = await calculate_cdek_delivery(
                session=session,
                from_location_code=from_code,
                to_location_code=to_code,
                packages=request.packages,
                date=request.date,
                currency=request.currency,
                lang=request.lang,
                delivery_type=request.delivery_type,
            )

            return DeliveryResponse(
                delivery_sum=result['delivery_sum'],
                period_min=result['period_min'],
                period_max=result['period_max'],
                service_name='СДЭК',
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f'CDEK API error: {str(e)}')
    else:
        raise HTTPException(status_code=400, detail='Unknown delivery service')