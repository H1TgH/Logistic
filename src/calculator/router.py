from fastapi import APIRouter, Depends, HTTPException
import asyncio

from src.database import SessionDep
from src.calculator.schemas import DeliveryRequest, DeliveryResponse, DeliveryResult
from src.cdek.utils import calculate_cdek_delivery, get_cdek_city_code, normalize_delivery_date_cdek
from src.pecom.utils import calculate_pecom_delivery
from src.dellin.utils import get_dellin_city_code, calculate_dellin_delivery


calculator_router = APIRouter(tags=['calculator'])

@calculator_router.post('/api/v1/public/calculate', response_model=DeliveryResponse)
async def calculate_delivery(
    request: DeliveryRequest,
    session: SessionDep,
):
    try:
        shipment_date = normalize_delivery_date_cdek(request.date)

        from_code = await get_cdek_city_code(session, request.from_location.city_name)
        to_code = await get_cdek_city_code(session, request.to_location.city_name)

        if from_code is None or to_code is None:
            raise HTTPException(status_code=400, detail='Не удалось определить код города')

        # Создаем корутины для каждого сервиса
        cdek_coroutine = calculate_cdek_delivery(
            session=session,
            from_location_code=from_code,
            to_location_code=to_code,
            packages=request.packages,
            date=shipment_date,
            currency=request.currency,
            lang=request.lang,
            delivery_type=request.delivery_type,
        )

        pecom_coroutine = calculate_pecom_delivery(
            from_city_name=request.from_location.city_name,
            to_city_name=request.to_location.city_name,
            packages=request.packages,
            delivery_type=request.delivery_type,
            session=session,
        )

        dellin_coroutine = calculate_dellin_delivery(
            session=session,
            from_location=request.from_location.city_name,
            to_location=request.to_location.city_name,
            packages=request.packages,
            delivery_type=request.delivery_type,
            date=shipment_date,
        )

        # Запускаем все корутины параллельно
        cdek_result, pecom_results, dellin_results = await asyncio.gather(
            cdek_coroutine,
            pecom_coroutine,
            dellin_coroutine,
            return_exceptions=True
        )

        results = []

        # Обрабатываем результаты CDEK
        if isinstance(cdek_result, Exception):
            print(f"CDEK API error: {str(cdek_result)}")
        else:
            results.append(
                DeliveryResult(
                    service_name='СДЭК',
                    delivery_sum=cdek_result['delivery_sum'],
                    period_min=cdek_result['period_min'],
                    period_max=cdek_result['period_max'],
                    service_url=cdek_result['service_url'],
                    service_logo=cdek_result['service_logo']
                )
            )

        # Обрабатываем результаты ПЭК
        if isinstance(pecom_results, Exception):
            print(f"Pecom API error: {str(pecom_results)}")
        else:
            for pecom_result in pecom_results:
                results.append(
                    DeliveryResult(
                        service_name=pecom_result['service_name'],
                        delivery_sum=pecom_result['delivery_sum'],
                        period_min=pecom_result['period_min'],
                        period_max=pecom_result['period_max'],
                        service_url=pecom_result['service_url'],
                        service_logo=pecom_result['service_logo']
                    )
                )

        # Обрабатываем результаты Деловых Линий
        if isinstance(dellin_results, Exception):
            print(f"Dellin API error: {str(dellin_results)}")
        else:
            for dellin_result in dellin_results:
                results.append(
                    DeliveryResult(
                        delivery_sum=dellin_result['delivery_sum'],
                        period_min=dellin_result['period_min'],
                        period_max=dellin_result['period_max'],
                        service_name=dellin_result['service_name'],
                        service_url=dellin_result['service_url'],
                        service_logo=dellin_result['service_logo'],
                    )
                )

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
    