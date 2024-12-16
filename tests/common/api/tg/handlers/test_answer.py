from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, User

from src.handlers.user_handlers.callback.task_callback import send_answer
from src.states.task_answer import TaskAnswerState


@pytest.mark.asyncio
async def test_send_answer(db_session):
    callback = MagicMock(spec=CallbackQuery)
    callback.data = 'send_answer:easy:1'
    callback.message = MagicMock()
    callback.message.message_id = 123
    callback.message.edit_text = AsyncMock()

    callback.from_user = MagicMock(spec=User)
    callback.from_user.id = 456

    state = MagicMock(spec=FSMContext)
    state.set_state = AsyncMock()
    state.update_data = AsyncMock()

    await send_answer(callback, state)

    state.set_state.assert_called_once_with(TaskAnswerState.waiting_for_answer)
    state.update_data.assert_any_call(message_id=123)
    state.update_data.assert_any_call(task_id='1')
    state.update_data.assert_any_call(user_id=456)

    callback.message.edit_text.assert_called_once_with(
        'Пришлите ваше решение в чат',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='Назад', callback_data='select_task:easy:1')],
            ]
        ),
    )
