from fastapi import APIRouter, Depends, HTTPException
from src.database import SessionDep
from src.calculator.schemas import DeliveryRequest, DeliveryResponse, DeliveryResult
from src.cdek.utils import calculate_cdek_delivery, get_city_code_by_name, normalize_delivery_date
from src.pecom.utils import calculate_pecom_delivery


calculator_router = APIRouter(tags=['calculator'])

@calculator_router.post('/api/v1/public/calculate', response_model=DeliveryResponse)
async def calculate_delivery(
    request: DeliveryRequest,
    session: SessionDep,
):
    try:
        shipment_date = normalize_delivery_date(request.date)

        from_code = await get_city_code_by_name(session, request.from_location.city_name)
        to_code = await get_city_code_by_name(session, request.to_location.city_name)

        if from_code is None or to_code is None:
            raise HTTPException(status_code=400, detail='Не удалось определить код города')

        results = []

        try:
            cdek_result = await calculate_cdek_delivery(
                session=session,
                from_location_code=from_code,
                to_location_code=to_code,
                packages=request.packages,
                date=shipment_date,
                currency=request.currency,
                lang=request.lang,
                delivery_type=request.delivery_type,
            )
            results.append(
                DeliveryResult(
                    delivery_sum=cdek_result['delivery_sum'],
                    period_min=cdek_result['period_min'],
                    period_max=cdek_result['period_max'],
                    service_name='СДЭК',
                )
            )
        except Exception as e:
            print(f"CDEK API error: {str(e)}")

        try:
            pecom_result = await calculate_pecom_delivery(
                from_city_id=request.from_location.city_name,
                to_city_id=request.to_location.city_name,
                packages=request.packages,
            )
            results.append(
                DeliveryResult(
                    delivery_sum=pecom_result['delivery_sum'],
                    period_min=pecom_result['period_min'],
                    period_max=pecom_result['period_max'],
                    service_name='ПЭК',
                )
            )
        except Exception as e:
            print(f"Pecom API error: {str(e)}")

        if not results:
            raise HTTPException(status_code=502, detail='Не удалось получить данные ни от одного сервиса')

        return DeliveryResponse(
            from_location=request.from_location,
            to_location=request.to_location,
            packages=request.packages,
            delivery_type=request.delivery_type,
            shipment_date=shipment_date,
            results=results,
        )

    except Exception as e:
        raise HTTPException(status_code=502, detail=f'API error: {str(e)}')