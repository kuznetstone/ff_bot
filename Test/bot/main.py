import asyncio
import logging

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from .config import BOT_TOKEN
from .database import init_db
from .handlers import main_menu, booking, my_bookings
from .keyboards.menus import main_menu_only_kb
from .states import NavStates, reset_history
from . import messages


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    await init_db()

    dp.include_router(main_menu.router)
    dp.include_router(booking.router)
    dp.include_router(my_bookings.router)

    error_router = Router()

    @error_router.errors()
    async def error_handler(event, exception):  # type: ignore[no-redef]
        logging.getLogger(__name__).error("Unhandled error: %s", exception)
        return True

    dp.include_router(error_router)

    fallback_router = Router()

    @fallback_router.message(F.text)
    async def fallback_handler(message: Message, state: FSMContext) -> None:
        await reset_history(state)
        await state.set_state(NavStates.MAIN_MENU)
        await message.answer(messages.UNKNOWN_COMMAND, reply_markup=main_menu_only_kb())

    dp.include_router(fallback_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
