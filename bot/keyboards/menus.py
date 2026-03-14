from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..services import get_categories, get_services_by_category, get_unique_services_by_category
from ..specialists import get_specialists
from ..time_slots import get_date_options, get_time_slots_for_date


def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Мои записи", callback_data="menu:my_bookings"),
        InlineKeyboardButton(text="Записаться", callback_data="menu:book"),
    )
    builder.adjust(1)
    return builder.as_markup()


def booking_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Выбрать услугу", callback_data="book:choose_service"),
        InlineKeyboardButton(text="Выбрать специалиста", callback_data="book:choose_specialist"),
        InlineKeyboardButton(text="Назад", callback_data="nav:back"),
    )
    builder.adjust(1)
    return builder.as_markup()


def categories_kb(specialist_name: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in get_categories(specialist_name):
        builder.add(
            InlineKeyboardButton(
                text=category,
                callback_data=f"book:category:{category}",
            )
        )
    builder.add(InlineKeyboardButton(text="Назад", callback_data="nav:back"))
    builder.adjust(1)
    return builder.as_markup()


def services_kb(category: str, specialist_name: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if specialist_name:
        services = get_services_by_category(category, specialist_name)
        for service in services:
            builder.add(
                InlineKeyboardButton(
                    text=service["name"],
                    callback_data=f"book:service:{service['id']}",
                )
            )
    else:
        services = get_unique_services_by_category(category)
        for service in services:
            builder.add(
                InlineKeyboardButton(
                    text=service["name"],
                    callback_data=f"book:service_unique:{service['id']}",
                )
            )
    builder.add(InlineKeyboardButton(text="Назад", callback_data="nav:back"))
    builder.adjust(1)
    return builder.as_markup()


def specialists_kb(allowed_names: list[str] | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for spec in get_specialists(allowed_names):
        builder.add(
            InlineKeyboardButton(
                text=spec["name"],
                callback_data=f"book:specialist:{spec['id']}",
            )
        )
    builder.add(InlineKeyboardButton(text="Назад", callback_data="nav:back"))
    builder.adjust(1)
    return builder.as_markup()


def dates_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, date_iso in get_date_options(15):
        builder.add(
            InlineKeyboardButton(
                text=label,
                callback_data=f"book:date:{date_iso}",
            )
        )
    builder.add(InlineKeyboardButton(text="Назад", callback_data="nav:back"))
    builder.adjust(5)
    return builder.as_markup()


def times_kb(date_iso: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, time_value in get_time_slots_for_date(date_iso):
        builder.add(
            InlineKeyboardButton(
                text=label,
                callback_data=f"book:time:{time_value}",
            )
        )
    builder.add(InlineKeyboardButton(text="Назад", callback_data="nav:back"))
    builder.adjust(2)
    return builder.as_markup()


def confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Подтвердить запись", callback_data="book:confirm"),
        InlineKeyboardButton(text="Назад", callback_data="nav:back"),
    )
    builder.adjust(1)
    return builder.as_markup()


def my_bookings_empty_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Записаться", callback_data="menu:book"))
    builder.adjust(1)
    return builder.as_markup()


def my_bookings_item_kb(booking_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Отменить запись",
            callback_data=f"booking:cancel:{booking_id}",
        )
    )
    builder.adjust(1)
    return builder.as_markup()


def cancel_confirm_kb(booking_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Подтвердить отмену",
            callback_data=f"booking:cancel_confirm:{booking_id}",
        ),
        InlineKeyboardButton(text="Назад", callback_data="nav:back"),
    )
    builder.adjust(1)
    return builder.as_markup()


def main_menu_only_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Главное меню", callback_data="menu:main"))
    builder.adjust(1)
    return builder.as_markup()


def my_bookings_only_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Мои записи", callback_data="menu:my_bookings"))
    builder.adjust(1)
    return builder.as_markup()
