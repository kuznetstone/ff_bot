from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

HISTORY_KEY = "state_history"


class NavStates(StatesGroup):
    MAIN_MENU = State()
    MY_BOOKINGS = State()
    BOOKING_MENU = State()
    SERVICE_CATEGORY = State()
    SERVICE = State()
    SPECIALIST = State()
    DATE = State()
    TIME = State()
    CONFIRM = State()
    CANCEL_CONFIRM = State()


async def reset_history(state: FSMContext) -> None:
    await state.update_data(**{HISTORY_KEY: []})


async def push_state(state: FSMContext, current_state: str | None) -> None:
    data = await state.get_data()
    history = data.get(HISTORY_KEY, [])
    if current_state:
        history.append(current_state)
    await state.update_data(**{HISTORY_KEY: history})


async def pop_state(state: FSMContext) -> str | None:
    data = await state.get_data()
    history = data.get(HISTORY_KEY, [])
    if not history:
        return None
    previous = history.pop()
    await state.update_data(**{HISTORY_KEY: history})
    return previous
