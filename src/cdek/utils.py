from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from sqlalchemy.future import select

from src.database import SessionDep
from src.models import DeliveryAPICredentials
from src.cdek.schemas import DeliveryPackage


CDEK_AUTH_URL = 'https://api.edu.cdek.ru/v2/oauth/token'
CDEK_CALC_URL = 'https://api.edu.cdek.ru/v2/calculator/tariff'
SERVICE_NAME = 'cdek'


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

from datetime import datetime, timezone

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

    payload = {
        'from_location': {'code': from_location_code},
        'to_location': {'code': to_location_code},
        'packages': [p.dict() for p in packages]
    }

    if tariff_code is not None:
        payload['tariff_code'] = tariff_code
    if date is not None:
        payload['date'] = date.isoformat()
    if currency is not None:
        payload['currency'] = currency
    if lang is not None:
        payload['lang'] = lang
    if delivery_type is not None:
        payload['type'] = delivery_type

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(CDEK_CALC_URL, json=payload, headers=headers)
        response.raise_for_status()

    return response.json()
