from __future__ import annotations

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

from .config import TIMEZONE
from . import messages

logger = logging.getLogger(__name__)

scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> AsyncIOScheduler:
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler(timezone=ZoneInfo(TIMEZONE))
        scheduler.start()
    return scheduler


def _job_id(booking_id: int, hours: int) -> str:
    return f"reminder_{booking_id}_{hours}h"


async def send_reminder(bot: Bot, user_id: int, service: str, specialist: str, date: str, time: str) -> None:
    text = messages.REMINDER_TEXT.format(
        service=service,
        specialist=specialist,
        date=date,
        time=time,
    )
    try:
        await bot.send_message(user_id, text)
        logger.info("Reminder sent to user=%s", user_id)
    except Exception as exc:
        logger.error("Failed to send reminder: %s", exc)


def schedule_reminders(
    bot: Bot,
    booking_id: int,
    user_id: int,
    service: str,
    specialist: str,
    date: str,
    time: str,
) -> None:
    scheduler_instance = start_scheduler()
    dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo(TIMEZONE))
    now = datetime.now(ZoneInfo(TIMEZONE))

    for hours in (24, 2):
        run_date = dt - timedelta(hours=hours)
        if run_date <= now:
            continue
        scheduler_instance.add_job(
            send_reminder,
            "date",
            run_date=run_date,
            id=_job_id(booking_id, hours),
            replace_existing=True,
            kwargs={
                "bot": bot,
                "user_id": user_id,
                "service": service,
                "specialist": specialist,
                "date": date,
                "time": time,
            },
        )
        logger.info("Reminder scheduled booking=%s %sh", booking_id, hours)


def remove_reminders(booking_id: int) -> None:
    if scheduler is None:
        return
    for hours in (24, 2):
        job_id = _job_id(booking_id, hours)
        job = scheduler.get_job(job_id)
        if job:
            scheduler.remove_job(job_id)
            logger.info("Reminder removed booking=%s %sh", booking_id, hours)
