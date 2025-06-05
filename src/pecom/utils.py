import httpx
import re
from src.calculator.schemas import DeliveryPackage

PECOM_CALC_URL = "http://calc.pecom.ru/bitrix/components/pecom/calc/ajax.php"
PECOM_CITIES_URL = "https://pecom.ru/ru/calc/towns.php"
DADATA_CLEAN_URL = "https://cleaner.dadata.ru/api/v1/clean/address"
PECOM_BASE_URL = 'https://pecom.ru'
PECOM_LOGO = 'https://pecom.ru/upload/medialibrary/3ba/logo.png'


async def clean_address_with_dadata(full_address: str) -> str:
    """Извлекает название города из полного адреса с помощью DaData API."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token ea8735bedf0b2f9eb7b423200c7c30cd6960b5cd",
        "X-Secret": "3417c8fabd698328580b9cc9fb621b3bfd299489",
    }
    payload = [full_address]

    async with httpx.AsyncClient() as client:
        response = await client.post(DADATA_CLEAN_URL, headers=headers, json=payload)
        response.raise_for_status()

    data = response.json()
    if not data:
        raise ValueError(f"DaData не вернул данные для адреса: {full_address}")

    result = data[0]
    city = result.get("city")
    if not city:
        city = result.get("region")
        if not city:
            raise ValueError(f"Не удалось извлечь город или регион из адреса: {full_address}")
    
    return city

async def get_pecom_city_code(city_name: str) -> int:
    """Получает код города ПЭК по его названию на основе справочника регионов."""
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
) -> list[dict]:
    if not packages:
        raise ValueError("Нет данных о посылке")

    # Извлекаем название города с помощью DaData
    from_city = await clean_address_with_dadata(from_city_name)
    to_city = await clean_address_with_dadata(to_city_name)

    # Получаем коды городов
    from_city_id = await get_pecom_city_code(from_city)
    to_city_id = await get_pecom_city_code(to_city)

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

    print(f"Параметры запроса к ПЭК: {params}")

    async with httpx.AsyncClient() as client:
        response = await client.get(PECOM_CALC_URL, params=params)
        response.raise_for_status()

    data = response.json()

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
        raise ValueError("Не удалось получить данные о стоимости доставки от ПЭК")

    return results