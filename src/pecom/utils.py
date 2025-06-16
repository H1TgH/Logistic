import httpx

import re

from src.calculator.schemas import DeliveryPackage
from sqlalchemy import select
from src.models import DadataCache
from src.database import SessionDep
from src.logger import setup_logger

PECOM_CALC_URL = "http://calc.pecom.ru/bitrix/components/pecom/calc/ajax.php"
PECOM_CITIES_URL = "https://pecom.ru/ru/calc/towns.php"
DADATA_CLEAN_URL = "https://dadata.ru/api/v1/clean/address"
PECOM_BASE_URL = 'https://pecom.ru'
PECOM_LOGO = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAIIAAAAZCAIAAABywGEqAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAA4RpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADw/eHBhY2tldCBiZWdpbj0i77u/IiBpZD0iVzVNME1wQ2VoaUh6cmVTek5UY3prYzlkIj8+IDx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IkFkb2JlIFhNUCBDb3JlIDUuNi1jMDY3IDc5LjE1Nzc0NywgMjAxNS8wMy8zMC0yMzo0MDo0MiAgICAgICAgIj4gPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4gPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIgeG1sbnM6eG1wTU09Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9tbS8iIHhtbG5zOnN0UmVmPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VSZWYjIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDoxMjMzNWFhYi1hOTJhLTA3NDktOWQ5My0yZjk0ZjhhOWQwZjMiIHhtcE1NOkRvY3VtZW50SUQ9InhtcC5kaWQ6MTUyMkJERUY2QTExMTFFQkJFQzhBQTI0MzlEMjdCREQiIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6MTUyMkJERUU2QTExMTFFQkJFQzhBQTI0MzlEMjdCREQiIHhtcDpDcmVhdG9yVG9vbD0iQWRvYmUgUGhvdG9zaG9wIENDIDIwMTUgKFdpbmRvd3MpIj4gPHhtcE1NOkRlcml2ZWRGcm9tIHN0UmVmOmluc3RhbmNlSUQ9InhtcC5paWQ6MjBmZWU3YWEtNDc5MS0yOTQ3LTkwZGUtM2JhZDZjOTNmNWNmIiBzdFJlZjpkb2N1bWVudElEPSJhZG9iZTpkb2NpZDpwaG90b3Nob3A6MWZmMzdkZmEtNmEwNi0xMWViLTk1M2Yt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'


logger = setup_logger('pecom')

async def clean_address_with_dadata(full_address: str, session: SessionDep) -> str:
    logger.info(f"Получен исходный адрес: {full_address}")
    
    result = await session.execute(
        select(DadataCache)
        .where(DadataCache.original_address == full_address)
    )
    cached_result = result.scalar_one_or_none()
    
    if cached_result:
        logger.info(f"Найден кэшированный результат для адреса: {full_address} -> {cached_result.cleaned_city}")
        return cached_result.cleaned_city

    logger.info(f"Отправка запроса к DaData для адреса: {full_address}")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token ab806e2870c628d3f2e326bd9883de220f22575b",
        "X-Secret": "410d3e0025682fc490bd8ea9ba671d18a3679b41",
    }
    payload = [full_address]

    async with httpx.AsyncClient() as client:
        response = await client.post(DADATA_CLEAN_URL, headers=headers, json=payload)
        response.raise_for_status()

    data = response.json()
    if not data:
        logger.error(f"DaData не вернул данные для адреса: {full_address}")
        raise ValueError(f"DaData не вернул данные для адреса: {full_address}")

    result = data[0]
    logger.info(f"Получен ответ от DaData: {result}")
    
    city = result.get("city")
    if not city:
        city = result.get("region")
        if not city:
            logger.error(f"Не удалось извлечь город или регион из адреса: {full_address}")
            raise ValueError(f"Не удалось извлечь город или регион из адреса: {full_address}")

    logger.info(f"Извлечен город: {city} из адреса: {full_address}")
    
    cache_entry = DadataCache(
        original_address=full_address,
        cleaned_city=city
    )
    session.add(cache_entry)
    await session.commit()
    logger.info(f"Результат сохранен в кэш: {full_address} -> {city}")
    
    return city

async def get_pecom_city_code(city_name: str) -> int:
    async with httpx.AsyncClient() as client:
        response = await client.get(PECOM_CITIES_URL)
        response.raise_for_status()
    
    data = response.json()
    for region, cities in data.items():
        for city_id, city_full_name in cities.items():
            extracted_city = city_full_name.lower()
            if extracted_city == city_name.lower():
                return int(city_id)
    raise ValueError(f"Код города для {city_name} не найден")

def extract_periods(aperiods: str, delivery_type: int) -> tuple[int, int]:
    """Извлекает минимальный и максимальный срок доставки из поля aperiods в зависимости от delivery_type."""
    # Соответствие delivery_type и типа доставки в aperiods
    delivery_types = {
        1: "склад - склад",  # ss
        2: "склад - дверь",  # sd
        3: "дверь - склад",  # ds
        4: "дверь - дверь",  # dd
    }
    delivery_key = delivery_types.get(delivery_type, "склад - склад")

    # Ищем строку, соответствующую нужному типу доставки
    pattern = rf"Количество суток в пути</b>: (\d+) - (\d+).*\({re.escape(delivery_key)}\)"
    match = re.search(pattern, aperiods)
    if match:
        period_min = int(match.group(1))
        period_max = int(match.group(2))
        return period_min, period_max
    # Если не нашли, используем значение по умолчанию из periods_days
    return 5, 5  # Можно доработать, если есть другие источники данных

async def calculate_pecom_delivery(
    from_city_name: str,
    to_city_name: str,
    delivery_type: int,
    packages: list[DeliveryPackage],
    session: SessionDep,
) -> list[dict]:
    if not packages:
        raise ValueError("Нет данных о посылке")

    logger.info(f"Расчет доставки ПЭК из {from_city_name} в {to_city_name}")
    
    # Получаем коды городов напрямую из оригинальных названий
    try:
        from_city_id = await get_pecom_city_code(from_city_name)
        to_city_id = await get_pecom_city_code(to_city_name)
        logger.info(f"Получены коды городов: {from_city_name} -> {from_city_id}, {to_city_name} -> {to_city_id}")
    except ValueError as e:
        logger.error(f"Ошибка при получении кодов городов: {str(e)}")
        raise

    package = packages[0]

    places = [
        package.width / 100,
        package.length / 100,
        package.height / 100,
        (package.width / 100) * (package.length / 100) * (package.height / 100),
        package.weight / 1000,
        0,
        0,
    ]

    params = {
        "places[0][]": places,
        "take[town]": from_city_id,
        "deliver[town]": to_city_id,
    }

    logger.info(f"Запрос расчета стоимости ПЭК. Параметры: {params}")

    async with httpx.AsyncClient() as client:
        response = await client.get(PECOM_CALC_URL, params=params)
        response.raise_for_status()

    data = response.json()
    logger.info(f"Ответ расчета стоимости ПЭК: {data}")

    # Базовая стоимость в зависимости от delivery_type
    base_price = 0.0
    if delivery_type == 2 and "deliver" in data and len(data["deliver"]) >= 3:
        base_price += int(data["deliver"][2])  # Склад - Дверь
    if delivery_type == 3 and "take" in data and len(data["take"]) >= 3:
        base_price += int(data["take"][2])  # Дверь - Склад
    if delivery_type == 4:
        if "deliver" in data and len(data["deliver"]) >= 3:
            base_price += int(data["deliver"][2])
        if "take" in data and len(data["take"]) >= 3:
            base_price += int(data["take"][2])  # Дверь - Дверь

    # Дополнительные услуги (страхование и т.д.)
    additional_cost = 0
    for add_key in ["ADD_1", "ADD_2", "ADD_3", "ADD_4"]:
        if add_key in data and "3" in data[add_key]:
            additional_cost += int(data[add_key]["3"])

    # Извлекаем сроки доставки из aperiods
    period_min, period_max = extract_periods(data.get("aperiods", ""), delivery_type)

    # Формируем результаты для auto и avia
    results = []
    if "auto" in data and len(data["auto"]) >= 3:
        auto_price = base_price + int(data["auto"][2]) + additional_cost
        results.append({
            "service_name": "ПЭК (автоперевозка)",
            "delivery_sum": auto_price,
            "period_min": period_min,
            "period_max": period_max,
            'service_url': PECOM_BASE_URL,
            'service_logo': PECOM_LOGO
        })

    if "avia" in data and len(data["avia"]) >= 3:
        avia_price = base_price + int(data["avia"][2]) + additional_cost
        results.append({
            "service_name": "ПЭК (авиаперевозка)",
            "delivery_sum": avia_price,
            "period_min": period_min,
            "period_max": period_max,
            'service_url': PECOM_BASE_URL,
            'service_logo': PECOM_LOGO
        })

    if not results:
        logger.error("Не удалось получить данные о стоимости доставки от ПЭК")
        raise ValueError("Не удалось получить данные о стоимости доставки от ПЭК")

    logger.info(f"Успешно получены результаты расчета ПЭК: {results}")
    return results