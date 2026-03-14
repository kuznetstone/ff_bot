from __future__ import annotations

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from ..states import NavStates, push_state, pop_state
from ..keyboards import menus
from .. import messages
from ..services import (
    get_service_by_id,
    get_unique_service_by_id,
    get_specialists_for_service_id,
    get_specialists_for_unique_service_id,
)
from ..specialists import get_specialist_by_id
from ..time_slots import get_time_slots_for_date
from ..database import add_booking
from ..scheduler import schedule_reminders
from ..config import SPECIALISTS
from .my_bookings import render_my_bookings

logger = logging.getLogger(__name__)

router = Router()


def _format_booking_preview(data: dict) -> str:
    return (
        f"{messages.CONFIRM_BOOKING_TITLE}\n\n"
        f"Услуга: {data.get('service_name', '')}\n"
        f"Специалист: {data.get('specialist_name', '')}\n"
        f"Дата: {data.get('date_display', '')}\n"
        f"Время: {data.get('time_value', '')}"
    )


async def _set_state_with_history(state: FSMContext, new_state) -> None:
    current = await state.get_state()
    await push_state(state, current)
    await state.set_state(new_state)


async def show_booking_menu(message: Message, state: FSMContext) -> None:
    await _set_state_with_history(state, NavStates.BOOKING_MENU)
    await message.answer(messages.BOOKING_MENU_TITLE, reply_markup=menus.booking_menu_kb())


async def render_state(message: Message, state: FSMContext, target_state: str) -> None:
    data = await state.get_data()
    if target_state == NavStates.BOOKING_MENU.state:
        await message.edit_text(messages.BOOKING_MENU_TITLE, reply_markup=menus.booking_menu_kb())
    elif target_state == NavStates.MAIN_MENU.state:
        await message.edit_text(messages.MAIN_MENU_TITLE, reply_markup=menus.main_menu_kb())
    elif target_state == NavStates.SERVICE_CATEGORY.state:
        await message.edit_text(
            messages.CHOOSE_SERVICE,
            reply_markup=menus.categories_kb(data.get("specialist_name")),
        )
    elif target_state == NavStates.SERVICE.state:
        category = data.get("category")
        specialist_name = data.get("specialist_name")
        if not category:
            await message.edit_text(
                messages.CHOOSE_SERVICE,
                reply_markup=menus.categories_kb(specialist_name),
            )
        else:
            services = menus.services_kb(category, specialist_name)
            await message.edit_text(messages.CHOOSE_SERVICE, reply_markup=services)
    elif target_state == NavStates.SPECIALIST.state:
        allowed = None
        service_id = data.get("service_id")
        if service_id:
            allowed = get_specialists_for_service_id(service_id)
        unique_service_id = data.get("unique_service_id")
        if unique_service_id:
            allowed = get_specialists_for_unique_service_id(unique_service_id)
        await message.edit_text(messages.CHOOSE_SPECIALIST, reply_markup=menus.specialists_kb(allowed))
    elif target_state == NavStates.DATE.state:
        await message.edit_text(messages.CHOOSE_DATE, reply_markup=menus.dates_kb())
    elif target_state == NavStates.TIME.state:
        date_iso = data.get("date_iso")
        if not date_iso:
            await message.edit_text(messages.CHOOSE_DATE, reply_markup=menus.dates_kb())
        else:
            if not get_time_slots_for_date(date_iso):
                await message.edit_text(messages.NO_SLOTS, reply_markup=menus.dates_kb())
            else:
                await message.edit_text(messages.CHOOSE_TIME, reply_markup=menus.times_kb(date_iso))
    elif target_state == NavStates.CONFIRM.state:
        await message.edit_text(_format_booking_preview(data), reply_markup=menus.confirm_kb())
    elif target_state == NavStates.MY_BOOKINGS.state:
        await render_my_bookings(message, state, edit=True, push_history=False)


@router.callback_query(F.data == "menu:book")
async def cb_booking_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await _set_state_with_history(state, NavStates.BOOKING_MENU)
    await callback.message.edit_text(messages.BOOKING_MENU_TITLE, reply_markup=menus.booking_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "book:choose_service")
async def cb_choose_service(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.update_data(
        category=None,
        service_id=None,
        unique_service_id=None,
        service_name=None,
        date_iso=None,
        date_display=None,
        time_value=None,
    )
    await _set_state_with_history(state, NavStates.SERVICE_CATEGORY)
    await callback.message.edit_text(
        messages.CHOOSE_SERVICE,
        reply_markup=menus.categories_kb(data.get("specialist_name")),
    )
    await callback.answer()


@router.callback_query(F.data == "book:choose_specialist")
async def cb_choose_specialist(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    allowed = None
    if data.get("service_id"):
        allowed = get_specialists_for_service_id(data["service_id"])
    if data.get("unique_service_id"):
        allowed = get_specialists_for_unique_service_id(data["unique_service_id"])
    await _set_state_with_history(state, NavStates.SPECIALIST)
    await callback.message.edit_text(messages.CHOOSE_SPECIALIST, reply_markup=menus.specialists_kb(allowed))
    await callback.answer()


@router.callback_query(F.data.startswith("book:category:"))
async def cb_category(callback: CallbackQuery, state: FSMContext) -> None:
    category = callback.data.split("book:category:")[-1]
    await state.update_data(category=category)
    data = await state.get_data()
    await _set_state_with_history(state, NavStates.SERVICE)
    await callback.message.edit_text(
        messages.CHOOSE_SERVICE,
        reply_markup=menus.services_kb(category, data.get("specialist_name")),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("book:service:"))
async def cb_service(callback: CallbackQuery, state: FSMContext) -> None:
    service_id = int(callback.data.split("book:service:")[-1])
    service = get_service_by_id(service_id)
    if not service:
        await callback.answer("Услуга не найдена", show_alert=True)
        return
    await state.update_data(service_id=service_id, service_name=service["name"], unique_service_id=None)

    data = await state.get_data()
    if data.get("specialist_name"):
        await _set_state_with_history(state, NavStates.DATE)
        await callback.message.edit_text(messages.CHOOSE_DATE, reply_markup=menus.dates_kb())
    else:
        allowed = get_specialists_for_service_id(service_id)
        await _set_state_with_history(state, NavStates.SPECIALIST)
        await callback.message.edit_text(messages.CHOOSE_SPECIALIST, reply_markup=menus.specialists_kb(allowed))
    await callback.answer()


@router.callback_query(F.data.startswith("book:service_unique:"))
async def cb_service_unique(callback: CallbackQuery, state: FSMContext) -> None:
    unique_id = int(callback.data.split("book:service_unique:")[-1])
    service = get_unique_service_by_id(unique_id)
    if not service:
        await callback.answer("Услуга не найдена", show_alert=True)
        return
    await state.update_data(
        unique_service_id=unique_id,
        service_id=None,
        service_name=service["name"],
        category=service["category"],
    )

    allowed = get_specialists_for_unique_service_id(unique_id)
    await _set_state_with_history(state, NavStates.SPECIALIST)
    await callback.message.edit_text(messages.CHOOSE_SPECIALIST, reply_markup=menus.specialists_kb(allowed))
    await callback.answer()


@router.callback_query(F.data.startswith("book:specialist:"))
async def cb_specialist(callback: CallbackQuery, state: FSMContext) -> None:
    spec_id = int(callback.data.split("book:specialist:")[-1])
    specialist = get_specialist_by_id(spec_id)
    if not specialist:
        await callback.answer("Специалист не найден", show_alert=True)
        return
    await state.update_data(specialist_id=spec_id, specialist_name=specialist["name"])
    data = await state.get_data()
    if not data.get("service_name"):
        await _set_state_with_history(state, NavStates.SERVICE_CATEGORY)
        await callback.message.edit_text(
            messages.CHOOSE_SERVICE,
            reply_markup=menus.categories_kb(specialist["name"]),
        )
    else:
        await _set_state_with_history(state, NavStates.DATE)
        await callback.message.edit_text(messages.CHOOSE_DATE, reply_markup=menus.dates_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("book:date:"))
async def cb_date(callback: CallbackQuery, state: FSMContext) -> None:
    date_iso = callback.data.split("book:date:")[-1]
    date_display = ".".join(reversed(date_iso.split("-")))
    await state.update_data(date_iso=date_iso, date_display=date_display)
    await _set_state_with_history(state, NavStates.TIME)

    if not get_time_slots_for_date(date_iso):
        await callback.message.edit_text(messages.NO_SLOTS, reply_markup=menus.dates_kb())
    else:
        await callback.message.edit_text(messages.CHOOSE_TIME, reply_markup=menus.times_kb(date_iso))
    await callback.answer()


@router.callback_query(F.data.startswith("book:time:"))
async def cb_time(callback: CallbackQuery, state: FSMContext) -> None:
    time_value = callback.data.split("book:time:")[-1]
    await state.update_data(time_value=time_value)
    await _set_state_with_history(state, NavStates.CONFIRM)
    data = await state.get_data()
    await callback.message.edit_text(_format_booking_preview(data), reply_markup=menus.confirm_kb())
    await callback.answer()


@router.callback_query(F.data == "book:confirm")
async def cb_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    user = callback.from_user

    if not all(
        [
            data.get("service_name"),
            data.get("specialist_name"),
            data.get("date_iso"),
            data.get("time_value"),
        ]
    ):
        await callback.answer("Заполните все шаги записи", show_alert=True)
        return

    try:
        booking_id = await add_booking(
            telegram_user_id=user.id,
            service=data.get("service_name", ""),
            specialist=data.get("specialist_name", ""),
            date=data.get("date_iso", ""),
            time=data.get("time_value", ""),
        )
        schedule_reminders(
            bot=callback.bot,
            booking_id=booking_id,
            user_id=user.id,
            service=data.get("service_name", ""),
            specialist=data.get("specialist_name", ""),
            date=data.get("date_iso", ""),
            time=data.get("time_value", ""),
        )

        specialist_id = SPECIALISTS.get(data.get("specialist_name", ""), 0)
        if specialist_id:
            client_name = user.username or str(user.id)
            notify_text = messages.NEW_BOOKING_NOTIFY.format(
                client=client_name,
                service=data.get("service_name", ""),
                date=data.get("date_display", ""),
                time=data.get("time_value", ""),
            )
            try:
                await callback.bot.send_message(specialist_id, notify_text)
            except Exception as exc:
                logger.error("Failed to notify specialist: %s", exc)

        await state.set_state(NavStates.MAIN_MENU)
        await callback.message.edit_text(messages.BOOKING_CREATED, reply_markup=menus.my_bookings_only_kb())
        await callback.answer()
    except Exception as exc:
        logger.error("Booking confirmation error: %s", exc)
        await callback.answer("Ошибка при создании записи", show_alert=True)


@router.callback_query(F.data == "nav:back")
async def cb_back(callback: CallbackQuery, state: FSMContext) -> None:
    previous = await pop_state(state)
    if not previous:
        await state.set_state(NavStates.MAIN_MENU)
        await callback.message.edit_text(messages.MAIN_MENU_TITLE, reply_markup=menus.main_menu_kb())
        await callback.answer()
        return

    await state.set_state(previous)
    await render_state(callback.message, state, previous)
    await callback.answer()
