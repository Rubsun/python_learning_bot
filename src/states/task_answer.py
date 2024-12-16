from aiogram.fsm.state import State, StatesGroup


class TaskAnswerState(StatesGroup):
    waiting_for_answer = State()
