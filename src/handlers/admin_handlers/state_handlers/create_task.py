import logging

import aio_pika
import msgpack
from aio_pika import ExchangeType
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from consumer.schema.task import CreateTaskMessage
from db.storage.rabbit import channel_pool
from src.handlers.admin_handlers.state_handlers.router import router
from src.keyboards.admin_kb import admin_complex_kb
from src.states.create_task import CreateTaskState


@router.message(CreateTaskState.waiting_for_title)
async def waiting_for_title(message: Message, state: FSMContext):
    title = message.text
    await state.update_data(title=title)
    await message.answer('Введите <b>описание задачи</b>', parse_mode='HTML')
    await state.set_state(CreateTaskState.waiting_for_description)


@router.message(CreateTaskState.waiting_for_description)
async def waiting_for_description(message: Message, state: FSMContext):
    description = message.text
    await state.update_data(description=description)
    await message.answer('Выберите <b>сложность задачи</b>', parse_mode='HTML', reply_markup=admin_complex_kb)


@router.callback_query(F.data.startswith('admin_complexity_'))
async def choose_complexity(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    complexity = callback.data.split('_')[2]
    print(complexity)
    await state.update_data(complexity=complexity)
    await callback.message.answer('Введите <b>исходные данные</b> для задачи', parse_mode='HTML')
    await state.set_state(CreateTaskState.waiting_for_input_data)


@router.message(CreateTaskState.waiting_for_input_data)
async def waiting_for_input_data(message: Message, state: FSMContext):
    input_data = message.text
    await state.update_data(input_data=input_data)
    await message.answer('Введите <b>ответ</b> на задачу', parse_mode='HTML')
    await state.set_state(CreateTaskState.waiting_for_correct_answer)


@router.message(CreateTaskState.waiting_for_correct_answer)
async def waiting_for_correct_answer(message: Message, state: FSMContext):
    correct_answer = message.text
    await state.update_data(correct_answer=correct_answer)
    await message.answer('Введите <b>секретный ответ</b>', parse_mode='HTML')
    await state.set_state(CreateTaskState.waiting_for_secret_answer)


@router.message(CreateTaskState.waiting_for_secret_answer)
async def waiting_for_secret_answer(message: Message, state: FSMContext):
    print('finally')
    secret_answer = message.text
    data = await state.get_data()
    try:
        async with channel_pool.acquire() as channel:  # type: aio_pika.Channel
            exchange = await channel.declare_exchange("user_tasks", ExchangeType.TOPIC, durable=True)
            await exchange.publish(
                aio_pika.Message(
                    msgpack.packb(
                        CreateTaskMessage(
                            title=data['title'],
                            description=data['description'],
                            complexity=data['complexity'],
                            input_data=data['input_data'],
                            correct_answer=data['correct_answer'],
                            secret_answer=secret_answer,
                            action='create_task',
                            event='task',
                        )
                    ),
                ),
                'user_messages',
            )
            print('Сообщение отправлено')
    except Exception as e:
        await message.answer('Что то пошло не так')
        logging.exception(e)
    await state.clear()
