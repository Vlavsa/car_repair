from aiogram.fsm.state import State, StatesGroup


class AddClient(StatesGroup):
    # Шаги состояний
    name = State()
    wait_phone = State()