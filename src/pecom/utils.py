import httpx
from src.calculator.schemas import DeliveryPackage


PECOM_CALC_URL = "http://calc.pecom.ru/bitrix/components/pecom/calc/ajax.php"

async def calculate_pecom_delivery(
    from_city_id: int,
    to_city_id: int,
    packages: list[DeliveryPackage]
) -> dict:
    if not packages:
        raise ValueError("Нет данных о посылке")

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

    print(params)

    async with httpx.AsyncClient() as client:
        response = await client.get(PECOM_CALC_URL, params=params)
        response.raise_for_status()

    data = response.json()

    if not data.get("price"):
        raise Exception(f"Ошибка ПЭК API: {data}")

    return {
        "delivery_sum": float(data["price"]),
        "period_min": int(data["transit"]["daysmin"]),
        "period_max": int(data["transit"]["daysmax"]),
        "service_name": "ПЭК"
    }
