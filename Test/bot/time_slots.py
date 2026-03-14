from __future__ import annotations

from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from typing import List, Tuple

from .config import TIMEZONE

WORK_START = time(9, 0)
WORK_END = time(21, 0)


def get_date_options(days: int = 15) -> List[Tuple[str, str]]:
    tz = ZoneInfo(TIMEZONE)
    today = datetime.now(tz).date()
    result = []
    for i in range(days):
        d = today + timedelta(days=i)
        result.append((d.strftime("%d.%m"), d.strftime("%Y-%m-%d")))
    return result


def get_time_slots_for_date(date_iso: str) -> List[Tuple[str, str]]:
    tz = ZoneInfo(TIMEZONE)
    target_date = datetime.strptime(date_iso, "%Y-%m-%d").date()
    now = datetime.now(tz)

    slots = []
    current = datetime.combine(target_date, WORK_START, tz)
    end = datetime.combine(target_date, WORK_END, tz)

    while current < end:
        next_hour = current + timedelta(hours=1)
        if target_date == now.date():
            if current <= now:
                current = next_hour
                continue
        label = f"{current.strftime('%H:%M')}–{next_hour.strftime('%H:%M')}"
        slots.append((label, current.strftime("%H:%M")))
        current = next_hour
    return slots
