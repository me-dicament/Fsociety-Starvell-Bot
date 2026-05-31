from aiogram.fsm.state import StatesGroup, State


class AutoRestoreFlow(StatesGroup):
    """Состояния для настройки автовосстановления лотов"""
    waiting_offer_id = State()
