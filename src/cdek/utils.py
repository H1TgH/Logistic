from datetime import datetime, timedelta, timezone, date, time
from typing import Optional

import httpx
from sqlalchemy.future import select

from src.database import SessionDep
from src.models import DeliveryAPICredentials
from src.cdek.schemas import DeliveryPackage


DELIVERY_TYPE_TO_TARIFF = {
    1: 136,  # Склад-Склад
    2: 137,  # Склад-Дверь
    3: 138,  # Дверь-Склад
    4: 139,  # Дверь-Дверь
}
CDEK_AUTH_URL = 'https://api.edu.cdek.ru/v2/oauth/token'
CDEK_CALC_URL = 'https://api.edu.cdek.ru/v2/calculator/tariff'
SERVICE_NAME = 'cdek'
CDEK_BASE_URL = 'https://www.cdek.ru/ru'
CDEK_LOGO = 'https://upload.wikimedia.org/wikipedia/commons/f/f8/CDEK_logo.svg'


async def get_cdek_token(session: SessionDep) -> str:
    now = datetime.now(timezone.utc)

    result = await session.execute(
        select(DeliveryAPICredentials).where(DeliveryAPICredentials.service_name == SERVICE_NAME)
    )
    creds = result.scalars().first()

    if creds and creds.token and creds.expires_at and creds.expires_at > now:
        return creds.token

    if not creds:
        creds = DeliveryAPICredentials(
            service_name=SERVICE_NAME,
            client_login='',
            client_secret='',
        )
        session.add(creds)
        await session.commit()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            CDEK_AUTH_URL,
            data={
                'grant_type': 'client_credentials',
                'client_id': creds.client_login,
                'client_secret': creds.client_secret,
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )

    if response.status_code != 200:
        raise Exception(f'Failed to get CDEK token: {response.text}')

    data = response.json()
    token = data['access_token']
    expires_in = data['expires_in']
    expires_at = now + timedelta(seconds=expires_in)

    if creds:
        creds.token = token
        creds.expires_at = expires_at
    else:
        creds = DeliveryAPICredentials(
            service_name=SERVICE_NAME,
            client_login='',
            client_secret='',
            token=token,
            expires_at=expires_at,
        )
        session.add(creds)

    await session.commit()
    return token

async def calculate_cdek_delivery(
    session: SessionDep,
    from_location_code: int,
    to_location_code: int,
    packages: list[DeliveryPackage],
    tariff_code: Optional[int] = None,
    date: Optional[datetime] = None,
    currency: Optional[int] = None,
    lang: Optional[str] = None,
    delivery_type: Optional[int] = None,
) -> dict:
    access_token = await get_cdek_token(session)

    if tariff_code is None:
        tariff_code = DELIVERY_TYPE_TO_TARIFF.get(delivery_type, 136)

    payload = {
        'tariff_code': tariff_code,
        'from_location': {'code': from_location_code},
        'to_location': {'code': to_location_code},
        'packages': [p.dict() for p in packages]
    }

    if date is not None:
        payload['date'] = date
    if currency is not None:
        payload['currency'] = currency
    if lang is not None:
        payload['lang'] = lang

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(CDEK_CALC_URL, json=payload, headers=headers)
        response.raise_for_status()

    data = response.json()
    data['service_url'] = CDEK_BASE_URL
    data['service_logo'] = CDEK_LOGO

    return data

async def get_cdek_city_code(session: SessionDep, city_name: str) -> Optional[int]:
    access_token = await get_cdek_token(session)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.edu.cdek.ru/v2/location/cities",
            headers={'Authorization': f'Bearer {access_token}'},
            params={'country_codes': 'RU', 'city': city_name}
        )
        if response.status_code != 200:
            print(f"Failed to fetch city code for '{city_name}': {response.text}")
            return None

        data = response.json()
        if isinstance(data, list) and data:
            return data[0]['code']

    return None

def normalize_delivery_date_cdek(user_date: datetime) -> str:
    user_date_only = user_date.date()
    today = date.today()

    if user_date_only <= today:
        corrected_date = today + timedelta(days=1)
    else:
        corrected_date = user_date_only

    full_datetime = datetime.combine(corrected_date, time(0, 0), timezone(timedelta(hours=3)))
    iso_string = full_datetime.isoformat()
    if iso_string.endswith('+03:00') or iso_string.endswith('+00:00'):
        iso_string = iso_string[:-3] + iso_string[-2:]
    return iso_string
