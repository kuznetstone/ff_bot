from __future__ import annotations

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from ..states import NavStates, push_state
from ..keyboards import menus
from ..database import get_user_bookings, get_booking, delete_booking
from ..scheduler import remove_reminders
from ..config import SPECIALISTS
from .. import messages

logger = logging.getLogger(__name__)

router = Router()


def _format_booking_item(booking: dict) -> str:
    date_display = ".".join(reversed(booking["date"].split("-")))
    return (
        f"Услуга: {booking['service']}\n"
        f"Специалист: {booking['specialist']}\n"
        f"Дата: {date_display}\n"
        f"Время: {booking['time']}"
    )


async def _set_state_with_history(state: FSMContext, new_state) -> None:
    current = await state.get_state()
    await push_state(state, current)
    await state.set_state(new_state)


async def render_my_bookings(
    message: Message,
    state: FSMContext,
    *,
    edit: bool = False,
    push_history: bool = True,
) -> None:
    if push_history:
        await _set_state_with_history(state, NavStates.MY_BOOKINGS)
    else:
        await state.set_state(NavStates.MY_BOOKINGS)

    bookings = await get_user_bookings(message.from_user.id)

    if not bookings:
        if edit:
            await message.edit_text(messages.NO_BOOKINGS, reply_markup=menus.my_bookings_empty_kb())
        else:
            await message.answer(messages.NO_BOOKINGS, reply_markup=menus.my_bookings_empty_kb())
        return

    if edit:
        await message.edit_text("Ваши записи:")
    else:
        await message.answer("Ваши записи:")

    for booking in bookings:
        text = _format_booking_item(booking)
        await message.answer(text, reply_markup=menus.my_bookings_item_kb(booking["id"]))


@router.callback_query(F.data == "menu:my_bookings")
async def cb_my_bookings(callback: CallbackQuery, state: FSMContext) -> None:
    await render_my_bookings(callback.message, state, edit=True, push_history=True)
    await callback.answer()


@router.callback_query(F.data.startswith("booking:cancel:"))
async def cb_cancel_booking(callback: CallbackQuery, state: FSMContext) -> None:
    booking_id = int(callback.data.split("booking:cancel:")[-1])
    await _set_state_with_history(state, NavStates.CANCEL_CONFIRM)
    await callback.message.edit_text(
        messages.BOOKING_CANCEL_CONFIRM,
        reply_markup=menus.cancel_confirm_kb(booking_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("booking:cancel_confirm:"))
async def cb_cancel_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    booking_id = int(callback.data.split("booking:cancel_confirm:")[-1])
    booking = await get_booking(booking_id)
    if not booking:
        await callback.answer("Запись не найдена", show_alert=True)
        return

    try:
        await delete_booking(booking_id)
        remove_reminders(booking_id)
        logger.info("Booking canceled id=%s user=%s", booking_id, callback.from_user.id)

        specialist_id = SPECIALISTS.get(booking["specialist"], 0)
        if specialist_id:
            try:
                await callback.bot.send_message(specialist_id, messages.CANCEL_NOTIFY)
            except Exception as exc:
                logger.error("Failed to notify specialist about cancel: %s", exc)

        await callback.message.edit_text(messages.BOOKING_CANCELED)
        await render_my_bookings(callback.message, state, edit=False, push_history=False)
        await callback.answer()
    except Exception as exc:
        logger.error("Cancel booking error: %s", exc)
        await callback.answer("Ошибка при отмене", show_alert=True)
