import asyncio
import logging
from asyncio import QueueEmpty

import aio_pika
import msgpack
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from config.settings import settings
from consumer.schema.task import GetTaskByIdMessage
from db.storage.rabbit import channel_pool
from src.bot import get_bot
from src.handlers.user_handlers.state_handlers.router import router
from src.logger import LOGGING_CONFIG
from src.metrics_init import RABBITMQ_MESSAGES_CONSUMED, RABBITMQ_MESSAGES_PRODUCED, measure_time
from src.states.task_answer import TaskAnswerState
from src.utils import check_user_task_solution


@router.message(TaskAnswerState.waiting_for_answer)
@measure_time
async def process_answer(message: Message, state: FSMContext):
    logging.config.dictConfig(LOGGING_CONFIG)
    python_code = message.text
    data = await state.get_data()
    task_id = data.get('task_id')
    message_id = data.get('message_id')
    user_id = data.get('user_id')
    bot = get_bot()
    await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message_id)

    async with channel_pool.acquire() as channel:
        exchange = await channel.declare_exchange('user_tasks', aio_pika.ExchangeType.TOPIC, durable=True)

        RABBITMQ_MESSAGES_PRODUCED.inc()
        await exchange.publish(
            aio_pika.Message(
                msgpack.packb(
                    GetTaskByIdMessage(
                        task_id=task_id,
                        user_id=user_id,
                        action='get_task_by_id',
                        event='tasks',
                    )
                ),
            ),
            'user_messages',
        )
        queue = await channel.declare_queue(
            settings.USER_TASK_QUEUE_TEMPLATE.format(user_id=message.from_user.id),
            durable=True,
        )
        retries = 3
        for _ in range(retries):
            try:
                q_task = await queue.get()
                task = msgpack.unpackb(q_task.body).get('task')
                if task:
                    RABBITMQ_MESSAGES_CONSUMED.inc()
                    break
            except QueueEmpty:
                await asyncio.sleep(0.02)

    result = await check_user_task_solution(python_code, task)

    await state.clear()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Попробовать снова', callback_data=f"select_task:{task.get('complexity')}:{task_id}"
                )
            ],
            [InlineKeyboardButton(text='Выбрать другую задачу', callback_data='get_another_task')],
        ]
    )
    if result.startswith('Решение неверное'):
        await message.answer(result, reply_markup=kb)
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
