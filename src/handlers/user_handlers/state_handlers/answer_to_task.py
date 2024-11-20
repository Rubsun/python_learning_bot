from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import Boolean
from sqlalchemy import select

from db.model.task import Task
from db.storage.db import async_session
from src.bot import get_bot
from src.handlers.user_handlers.state_handlers.router import router
from src.states.task_answer import TaskAnswerState
from src.utils import check_user_task_solution


@router.message(TaskAnswerState.waiting_for_answer)
async def process_answer(message: Message, state: FSMContext):
    python_code = message.text
    data = await state.get_data()
    task_id = data.get('task_id')
    message_id = data.get('message_id')
    bot = get_bot()
    await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message_id)
    async with async_session() as db:
        task = await db.scalar(select(Task).where(Task.id == task_id))

    result = await check_user_task_solution(python_code, task)

    await state.clear()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Попробовать снова', callback_data=f'select_task:{task.complexity}:{task_id}')],
            [InlineKeyboardButton(text='Выбрать другую задачу', callback_data='get_another_task')],
        ]
    )
    if result == 'Решение неверное ❌':
        await message.answer(result, reply_markup=kb)
    elif result == '':
        await message.answer('пусто', reply_markup=kb)

    else:
        await message.answer(
            result,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text='Выбрать следующую задачу', callback_data='get_another_task')]
                ]
            ),
            parse_mode='HTML',
        )
