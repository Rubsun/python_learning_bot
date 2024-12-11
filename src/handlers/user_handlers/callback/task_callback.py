import asyncio

import aio_pika
import msgpack
from aio_pika import ExchangeType
from aio_pika.exceptions import QueueEmpty
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from src.metrics_init import RABBITMQ_MESSAGES_CONSUMED, RABBITMQ_MESSAGES_PRODUCED, measure_time
from config.settings import settings
from consumer.schema.task import TaskMessage, GetTaskByIdMessage
from db.storage.rabbit import channel_pool
from src.handlers.user_handlers.callback.router import router
from src.keyboards.user_kb import complex_kb, generate_carousel_keyboard
from src.states.task_answer import TaskAnswerState


@router.callback_query(F.data == 'get_complexity')
@measure_time
async def get_complexity(callback: CallbackQuery):
    txt = 'Выберите уровень сложности'
    await callback.message.answer(text=txt, reply_markup=complex_kb)


@router.callback_query(F.data == 'get_another_task')
@measure_time
async def get_another_task(callback: CallbackQuery):
    txt = 'Выберите уровень сложности'
    await callback.message.edit_text(text=txt, reply_markup=complex_kb)


@router.callback_query(F.data.startswith('complexity_'))
@measure_time
async def get_tasks(callback: CallbackQuery):
    complexity = callback.data.split('_')[1]  # это сложность: easy, normal, hard

    async with channel_pool.acquire() as channel:  # type: aio_pika.Channel
        exchange = await channel.declare_exchange("user_tasks", ExchangeType.TOPIC, durable=True)

        RABBITMQ_MESSAGES_PRODUCED.inc()
        await exchange.publish(
            aio_pika.Message(
                msgpack.packb(
                    TaskMessage(
                        user_id=callback.from_user.id,
                        action=f'get_tasks_by_complexity:{complexity}',
                        event='tasks',
                    )
                ),
            ),
            'user_messages',
        )
        queue = await channel.declare_queue(
            settings.USER_TASK_QUEUE_TEMPLATE.format(user_id=callback.from_user.id),
            durable=True,
        )
        retries = 3
        for _ in range(retries):
            try:
                tasks = await queue.get()
                parsed_tasks = msgpack.unpackb(tasks.body).get('tasks')
                if parsed_tasks:
                    RABBITMQ_MESSAGES_CONSUMED.inc()
                    break
            except QueueEmpty:
                await asyncio.sleep(0.02)

    print('Parsed_task: ', parsed_tasks)
    kb = await generate_carousel_keyboard(parsed_tasks, f'select_task:{complexity}')
    txt = f'Сложность: <b>{complexity}</b>'
    await callback.message.edit_text(text=txt, reply_markup=kb, parse_mode='HTML')


@router.callback_query(F.data.regexp(r'^select_task:(hard|easy|normal):(next|prev):\d+$'))
@measure_time
async def handle_carousel(callback: CallbackQuery):
    data = callback.data.split(':')
    page = int(data[3]) if len(data) > 3 else 0
    complexity = data[1]

    async with channel_pool.acquire() as channel:  # type: aio_pika.Channel
        exchange = await channel.declare_exchange("user_tasks", ExchangeType.TOPIC, durable=True)

        RABBITMQ_MESSAGES_PRODUCED.inc()
        await exchange.publish(
            aio_pika.Message(
                msgpack.packb(
                    TaskMessage(
                        user_id=callback.from_user.id,
                        action=f'get_tasks_by_complexity:{complexity}',
                        event='tasks',
                    )
                ),
            ),
            'user_messages',
        )
        queue = await channel.declare_queue(
            settings.USER_TASK_QUEUE_TEMPLATE.format(user_id=callback.from_user.id),
            durable=True,
        )
        retries = 3
        for _ in range(retries):
            try:
                tasks = await queue.get()
                parsed_tasks = msgpack.unpackb(tasks.body).get('tasks')
                if parsed_tasks:
                    RABBITMQ_MESSAGES_CONSUMED.inc()
                    break
            except QueueEmpty:
                await asyncio.sleep(0.02)

    if parsed_tasks:
        keyboard = await generate_carousel_keyboard(parsed_tasks, f'select_task:{complexity}', page)
        await callback.message.edit_text(
            text=f'Сложность: <b>{complexity}</b>', reply_markup=keyboard, parse_mode='HTML'
        )
        # await callback.message.edit_reply_markup(reply_markup=keyboard)
    else:
        await callback.message.answer('Нет данных для отображения.')


@router.callback_query(F.data.startswith('select_task:'))
@measure_time
async def chosen_task(callback: CallbackQuery, state: FSMContext):
    print('CALLBACK', callback.data)
    await state.clear()
    _, complexity, task_id = callback.data.split(':')
    async with channel_pool.acquire() as channel:  # type: aio_pika.Channel
        exchange = await channel.declare_exchange("user_tasks", ExchangeType.TOPIC, durable=True)

        RABBITMQ_MESSAGES_PRODUCED.inc()
        await exchange.publish(
            aio_pika.Message(
                msgpack.packb(
                    GetTaskByIdMessage(
                        task_id=task_id,
                        user_id=callback.from_user.id,
                        action='get_task_by_id',
                        event='tasks',
                    )
                ),
            ),
            'user_messages',
        )
        queue = await channel.declare_queue(
            settings.USER_TASK_QUEUE_TEMPLATE.format(user_id=callback.from_user.id),
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

    title_text = f"<b>Задача: {task['title']}</b>"
    complexity_text = f"Сложность: {task['complexity']}"
    description_text = f"Описание: {task['description']}"

    texts_to_send = [title_text, complexity_text, description_text]
    full_text = '\n'.join(texts_to_send)
    max_length = 4096

    task_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Отправить решение', callback_data=f'send_answer:{complexity}:{task_id}')],
            [InlineKeyboardButton(text='Выбрать другую задачу', callback_data='get_another_task')],
        ]
    )

    if len(full_text) < max_length:
        await callback.message.edit_text(text=full_text, parse_mode='HTML', reply_markup=task_kb)
    else:
        for text in texts_to_send[:-2]:
            await callback.message.answer(text, parse_mode='HTML')
        await callback.message.answer(text=texts_to_send[-1], reply_markup=task_kb)


@router.callback_query(F.data.startswith('send_answer:'))
@measure_time
async def send_answer(callback: CallbackQuery, state: FSMContext):
    _, complexity, task_id = callback.data.split(':')

    await state.set_state(TaskAnswerState.waiting_for_answer)
    await state.update_data(message_id=callback.message.message_id)
    await state.update_data(task_id=task_id)

    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Назад', callback_data=f'select_task:{complexity}:{task_id}')],
        ]
    )

    await callback.message.edit_text('Пришлите ваше решение в чат', reply_markup=back_kb)
