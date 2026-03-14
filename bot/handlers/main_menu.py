from __future__ import annotations

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from ..states import NavStates, reset_history
from ..keyboards.menus import main_menu_kb
from .. import messages

logger = logging.getLogger(__name__)

router = Router()


async def show_main_menu(message: Message, state: FSMContext) -> None:
    await reset_history(state)
    await state.set_state(NavStates.MAIN_MENU)
    await message.answer(messages.MAIN_MENU_TITLE, reply_markup=main_menu_kb())


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await show_main_menu(message, state)


@router.callback_query(F.data == "menu:main")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await reset_history(state)
    await state.set_state(NavStates.MAIN_MENU)
    await callback.message.edit_text(messages.MAIN_MENU_TITLE, reply_markup=main_menu_kb())
    await callback.answer()
