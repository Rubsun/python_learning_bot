from asyncio import QueueEmpty
import logging

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
import aio_pika
import msgpack
import asyncio
from config.settings import settings
from src.logger import logger, LOGGING_CONFIG

from consumer.schema.task import GetTaskByIdMessage
from db.storage.rabbit import channel_pool
from src.metrics_init import measure_time, RABBITMQ_MESSAGES_PRODUCED, RABBITMQ_MESSAGES_CONSUMED
from src.bot import get_bot
from src.handlers.user_handlers.state_handlers.router import router
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
    logger.debug(f'user_id: {user_id}, task_id: {task_id}')

    async with channel_pool.acquire() as channel:  # type: aio_pika.Channel
        exchange = await channel.declare_exchange("user_tasks", aio_pika.ExchangeType.TOPIC, durable=True)

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
                    logger.debug(f'TASK:\n{task}')
                    RABBITMQ_MESSAGES_CONSUMED.inc()
                    break
            except QueueEmpty:
                await asyncio.sleep(0.02)

    logger.debug(f'TASK:\n{task}')
    result = await check_user_task_solution(python_code, task)

    await state.clear()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Попробовать снова', callback_data=f'select_task:{task.get('complexity')}:{task_id}'
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
