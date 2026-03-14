from __future__ import annotations

import logging
from typing import List, Dict, Any

import requests

from .config import YCLIENTS_BASE_URL, YCLIENTS_TOKEN, YCLIENTS_COMPANY_ID

logger = logging.getLogger(__name__)


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {YCLIENTS_TOKEN}",
        "Content-Type": "application/json",
    }


def get_services() -> List[Dict[str, Any]]:
    """
    Получение услуг из YCLIENTS.
    Сейчас возвращает mock-данные, но структура готова к реальному API.
    """
    if not YCLIENTS_TOKEN or not YCLIENTS_COMPANY_ID:
        return [
            {"id": 1, "title": "СПА Релакс"},
            {"id": 2, "title": "Классический массаж"},
        ]

    try:
        url = f"{YCLIENTS_BASE_URL}/api/v1/services/{YCLIENTS_COMPANY_ID}"
        resp = requests.get(url, headers=_headers(), timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])
    except Exception as exc:
        logger.error("YCLIENTS get_services error: %s", exc)
        raise


def get_staff() -> List[Dict[str, Any]]:
    if not YCLIENTS_TOKEN or not YCLIENTS_COMPANY_ID:
        return [
            {"id": 1, "name": "Марина"},
            {"id": 2, "name": "Елизавета"},
        ]

    try:
        url = f"{YCLIENTS_BASE_URL}/api/v1/staff/{YCLIENTS_COMPANY_ID}"
        resp = requests.get(url, headers=_headers(), timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])
    except Exception as exc:
        logger.error("YCLIENTS get_staff error: %s", exc)
        raise


def get_available_slots(service_id: int, staff_id: int, date: str) -> List[Dict[str, Any]]:
    if not YCLIENTS_TOKEN or not YCLIENTS_COMPANY_ID:
        return [
            {"time": "09:00"},
            {"time": "10:00"},
        ]

    try:
        url = f"{YCLIENTS_BASE_URL}/api/v1/book_times/{YCLIENTS_COMPANY_ID}"
        params = {"service_ids": service_id, "staff_id": staff_id, "date": date}
        resp = requests.get(url, headers=_headers(), params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])
    except Exception as exc:
        logger.error("YCLIENTS get_available_slots error: %s", exc)
        raise


def create_booking(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not YCLIENTS_TOKEN or not YCLIENTS_COMPANY_ID:
        return {"success": True, "booking_id": 1, "message": "Mock booking created"}

    try:
        url = f"{YCLIENTS_BASE_URL}/api/v1/book_record/{YCLIENTS_COMPANY_ID}"
        resp = requests.post(url, headers=_headers(), json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.error("YCLIENTS create_booking error: %s", exc)
        raise
