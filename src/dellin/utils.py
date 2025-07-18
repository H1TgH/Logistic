from datetime import datetime, timedelta
import httpx
import json
import os
from typing import Optional

from sqlalchemy import select

from src.models import DeliveryAPICredentials
from src.database import SessionDep
from src.calculator.schemas import DeliveryPackage
from src.pecom.utils import clean_address_with_dadata
from src.logger import setup_logger


logger = setup_logger('dellin')

AVAILABLE_DELIVERY_TYPE = ['auto', 'express', 'avia']

DELLIN_BASE_URL = 'https://www.dellin.ru'
DELLIN_LOGO = 'https://www.ph4.ru/DL/LOGO/d/dellin__.gif'

current_dir = os.path.dirname(os.path.abspath(__file__))
terminals_path = os.path.join(current_dir, 'terminals_v3.json')

def load_terminals(file_path: str) -> dict:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError(f"Файл {file_path} не является валидным JSON-словарём")
            return data
    except FileNotFoundError:
        raise FileNotFoundError(f"Файл {file_path} не найден")
    except json.JSONDecodeError as e:
        raise ValueError(f"Ошибка парсинга JSON в файле {file_path}: {str(e)}")

def get_terminal_id(city_code: str, terminals_data: dict, delivery_mode: str) -> Optional[str]:
    if not isinstance(terminals_data, dict):
        raise TypeError(f"terminals_data должен быть словарем, получен {type(terminals_data)}")
    
    for city in terminals_data.get('city', []):
        if city.get('code') == city_code:
            terminals = city.get('terminals', {}).get('terminal', [])
            for terminal in terminals:
                if not terminal.get('giveoutCargo', True):
                    continue
                if delivery_mode == 'express':
                    if terminal.get('express', False):
                        print(f"Выбран терминал для {city_code} и {delivery_mode}: {terminal.get('id')} ({terminal.get('name')})")
                        return terminal.get('id')
                else:
                    print(f"Выбран терминал для {city_code} и {delivery_mode}: {terminal.get('id')} ({terminal.get('name')})")
                    return terminal.get('id')
            print(f"Терминал для города с кодом {city_code} и типом доставки {delivery_mode} не найден")
            return None
    print(f"Город с кодом {city_code} не найден в справочнике")
    return None

TERMINALS_DATA = load_terminals(terminals_path)
print(f"TERMINALS_DATA: {TERMINALS_DATA}, type: {type(TERMINALS_DATA)}")

async def get_dellin_token(session: SessionDep) -> str:
    result = await session.execute(
        select(DeliveryAPICredentials)
        .where(DeliveryAPICredentials.service_name == 'dellin')
    )
    creds = result.scalars().first()

    if not creds or not creds.token:
        raise ValueError("Токен для Деловых Линий не найден в базе данных")

    return creds.token

async def get_dellin_city_code(session: SessionDep, city_name: str) -> str:
    appkey = await get_dellin_token(session)

    logger.info(f"Запрос кода города Деловых Линий. Город: {city_name}")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'https://api.dellin.ru/v2/public/kladr.json',
            json={'appkey': appkey, 'q': city_name}
        )
        
        if response.status_code != 200:
            logger.error(f"Ошибка получения кода города Деловых Линий. Статус: {response.status_code}, Ответ: {response.text}")
            return None
        
        data = response.json()
        logger.info(f"Ответ поиска города Деловых Линий: {data}")
        cities = data.get('cities', [])
        if not cities:
            logger.error(f"Город '{city_name}' не найден в API Деловых Линий")
            return None
        
        return cities[0].get('code')

async def calculate_dellin_delivery(
    session: SessionDep,
    from_location: str,
    to_location: str,
    packages: list,
    delivery_type: int,
    date: str
) -> list[dict]:
    if not packages:
        raise ValueError("Нет данных о посылке")

    appkey = await get_dellin_token(session)

    # Используем оригинальные названия городов
    from_city_code = await get_dellin_city_code(session, from_location)
    to_city_code = await get_dellin_city_code(session, to_location)

    if not from_city_code or not to_city_code:
        raise ValueError(f"Не удалось определить коды городов: {from_location} -> {to_city_code}")

    package = packages[0]

    # Преобразуем строку даты в объект datetime
    try:
        produce_date = datetime.fromisoformat(date.replace('+0300', '+03:00')).replace(tzinfo=None)
    except ValueError as e:
        try:
            produce_date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError as e:
            raise ValueError(f"Неверный формат даты: {date}, ожидается 'ГГГГ-ММ-ДД' или ISO формат") from e

    # Определяем варианты доставки (derival и arrival) в зависимости от delivery_type
    derival_variant = 'terminal' if delivery_type in [1, 2] else 'address'
    arrival_variant = 'terminal' if delivery_type in [1, 3] else 'address'

    results = []

    # Выполняем запрос для каждого доступного типа доставки
    async with httpx.AsyncClient() as client:
        for delivery_mode in AVAILABLE_DELIVERY_TYPE:
            # Получаем terminalID для текущего типа доставки
            from_terminal_id = get_terminal_id(from_city_code, TERMINALS_DATA, delivery_mode) if derival_variant == 'terminal' else None
            to_terminal_id = get_terminal_id(to_city_code, TERMINALS_DATA, delivery_mode) if arrival_variant == 'terminal' else None

            if not from_terminal_id or not to_terminal_id:
                logger.warning(f"Пропускаем {delivery_mode}, так как не найдены подходящие терминалы")
                continue

            # Формируем payload
            payload = {
                'appkey': appkey,
                'delivery': {
                    'deliveryType': {
                        'type': delivery_mode
                    },
                    'derival': {
                        'produceDate': produce_date.strftime('%Y-%m-%d'),
                        'variant': derival_variant,
                        'terminalID': from_terminal_id
                    },
                    'arrival': {
                        'variant': arrival_variant,
                        'terminalID': to_terminal_id
                    }
                },
                'cargo': {
                    'quantity': 1,
                    'length': package.length / 100,
                    'width': package.width / 100,
                    'height': package.height / 100,
                    'weight': package.weight / 1000,
                    'totalVolume': (package.length / 100) * (package.width / 100) * (package.height / 100),
                    'totalWeight': package.weight / 1000,
                    'insurance': {
                        'statedValue': 1000.0,
                        'term': True
                    }
                },
                'payment': {
                    'type': 'cash',
                    'paymentCity': from_city_code
                }
            }

            logger.info(f"Запрос расчета стоимости Деловых Линий ({delivery_mode}). Параметры: {payload}")
            try:
                response = await client.post(
                    'https://api.dellin.ru/v2/calculator.json',
                    json=payload
                )
                response.raise_for_status()

                data = response.json()
                logger.info(f"Ответ расчета стоимости Деловых Линий ({delivery_mode}): {data}")

                # Извлекаем данные из ответа
                if data.get('metadata', {}).get('status') != 200:
                    logger.error(f"Ошибка API Деловых Линий для {delivery_mode}: {data}")
                    continue

                response_data = data.get('data', {})
                
                # Стоимость доставки
                price = response_data.get('price', 0)
                if not price:
                    price = response_data.get(delivery_mode, {}).get('price', 0)
                    if not price:
                        logger.error(f"Не удалось получить стоимость доставки для {delivery_mode}")
                        continue

                # Сроки доставки
                period_min = response_data.get('period', {}).get('min', 0)
                period_max = response_data.get('period', {}).get('max', 0)

                results.append({
                    'delivery_sum': price,
                    'period_min': period_min,
                    'period_max': period_max,
                    'service_name': f'Деловые Линии ({delivery_mode})',
                    'service_url': DELLIN_BASE_URL,
                    'service_logo': DELLIN_LOGO,
                })

            except Exception as e:
                logger.error(f"Ошибка при расчете стоимости Деловых Линий ({delivery_mode}): {str(e)}")
                continue

    if not results:
        logger.error("Не удалось получить данные о стоимости доставки от Деловых Линий")
        raise ValueError("Не удалось получить данные о стоимости доставки от Деловых Линий")

    logger.info(f"Успешно получены результаты расчета Деловых Линий: {results}")
    return results