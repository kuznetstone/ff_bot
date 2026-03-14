from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any

import aiosqlite

from .config import DATABASE_PATH, TIMEZONE
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


async def init_db() -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER NOT NULL,
                service TEXT NOT NULL,
                specialist TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        await db.commit()


async def add_booking(
    telegram_user_id: int,
    service: str,
    specialist: str,
    date: str,
    time: str,
) -> int:
    created_at = datetime.now(ZoneInfo(TIMEZONE)).isoformat(timespec="seconds")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO bookings (telegram_user_id, service, specialist, date, time, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (telegram_user_id, service, specialist, date, time, created_at),
        )
        await db.commit()
        booking_id = cursor.lastrowid
        logger.info("Booking created id=%s user=%s", booking_id, telegram_user_id)
        return booking_id


async def get_user_bookings(telegram_user_id: int) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM bookings
            WHERE telegram_user_id = ?
            ORDER BY date, time
            """,
            (telegram_user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_booking(booking_id: int) -> Dict[str, Any] | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM bookings WHERE id = ?",
            (booking_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def delete_booking(booking_id: int) -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        await db.commit()
        logger.info("Booking deleted id=%s", booking_id)
