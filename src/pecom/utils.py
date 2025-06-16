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
PECOM_LOGO = 'https://pecom.ru/local/vue-cli-build/images/logo.svg'

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