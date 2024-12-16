from aiogram.fsm.state import StatesGroup, State


class CreateTaskState(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_complexity = State()
    waiting_for_correct_answer = State()
    waiting_for_input_data = State()
    waiting_for_secret_answer = State()
    waiting_for_input_test_count = State()
    waiting_for_input_test = State()
    waiting_for_secret_test_count = State()
    waiting_for_secret_test = State()
