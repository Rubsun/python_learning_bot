from aiogram import types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext

from src.handlers.admin_handlers.command.router import router
from src.states.create_task import CreateTaskState


@router.message(Command('create_task'))
async def create_task(message: types.Message, state: FSMContext):
    await message.answer(text='Введите название задачи')
    await state.set_state(CreateTaskState.waiting_for_title)
