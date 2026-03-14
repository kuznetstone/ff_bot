from __future__ import annotations

import logging
from typing import List, Dict, Any
from pathlib import Path

from openpyxl import load_workbook

from .config import EXCEL_SERVICES_PATH
from . import yclients_api

logger = logging.getLogger(__name__)

DEFAULT_SERVICES = [
    {"specialist": "Марина", "category": "СПА", "name": "СПА Релакс"},
    {"specialist": "Марина", "category": "Массаж", "name": "Классический массаж"},
    {"specialist": "Елизавета", "category": "СПА Turkish", "name": "Turkish Classic"},
    {"specialist": "Ирина", "category": "Массаж", "name": "Лимфодренажный массаж"},
    {"specialist": "Татьяна", "category": "Арома программы", "name": "Арома Баланс"},
]

_SERVICES_CACHE: List[Dict[str, Any]] = []


def _normalize_header(value: str) -> str:
    return value.strip().lower()


def _load_from_excel() -> List[Dict[str, Any]]:
    path = Path(EXCEL_SERVICES_PATH)
    if not path.exists():
        logger.warning("Excel services file not found: %s", path)
        return []

    wb = load_workbook(filename=path, read_only=True, data_only=True)
    if "services" in wb.sheetnames:
        ws = wb["services"]
    else:
        ws = wb.active

    rows = ws.iter_rows(values_only=True)
    try:
        headers = next(rows)
    except StopIteration:
        return []

    header_map = {}
    for idx, h in enumerate(headers):
        if not h:
            continue
        key = _normalize_header(str(h))
        header_map[key] = idx

    def col_index(*names: str) -> int | None:
        for name in names:
            idx = header_map.get(_normalize_header(name))
            if idx is not None:
                return idx
        return None

    specialist_col = col_index("specialist", "специалист")
    category_col = col_index("category", "категория", "type", "тип")
    service_col = col_index("service", "услуга")

    if specialist_col is None or category_col is None or service_col is None:
        logger.error("Excel header columns not found. Required: specialist/category/service")
        return []

    result = []
    for row in rows:
        specialist = row[specialist_col] if specialist_col < len(row) else None
        category = row[category_col] if category_col < len(row) else None
        service = row[service_col] if service_col < len(row) else None
        if not specialist or not category or not service:
            continue
        result.append(
            {
                "specialist": str(specialist).strip(),
                "category": str(category).strip(),
                "name": str(service).strip(),
            }
        )
    return result


def _ensure_cache() -> None:
    global _SERVICES_CACHE
    if _SERVICES_CACHE:
        return

    from_excel = _load_from_excel()
    raw = from_excel if from_excel else DEFAULT_SERVICES

    _SERVICES_CACHE = [
        {"id": idx + 1, **item}
        for idx, item in enumerate(raw)
    ]


def get_categories(specialist_name: str | None = None) -> List[str]:
    _ensure_cache()
    services = _SERVICES_CACHE
    if specialist_name:
        services = [s for s in services if s["specialist"] == specialist_name]
    categories = sorted({s["category"] for s in services})
    return categories


def get_services_by_category(category: str, specialist_name: str | None = None) -> List[Dict[str, Any]]:
    _ensure_cache()
    services = _SERVICES_CACHE
    if specialist_name:
        services = [s for s in services if s["specialist"] == specialist_name]
    return [s for s in services if s["category"] == category]


def get_service_by_id(service_id: int) -> Dict[str, Any] | None:
    _ensure_cache()
    for service in _SERVICES_CACHE:
        if service["id"] == service_id:
            return service
    return None


def get_specialists_for_service_id(service_id: int) -> List[str]:
    _ensure_cache()
    service = get_service_by_id(service_id)
    if not service:
        return []
    name = service["name"]
    return sorted({s["specialist"] for s in _SERVICES_CACHE if s["name"] == name})


def get_services_from_api() -> List[Dict[str, Any]]:
    try:
        return yclients_api.get_services()
    except Exception as exc:
        logger.warning("YCLIENTS get_services failed, using local data: %s", exc)
        _ensure_cache()
        return _SERVICES_CACHE
