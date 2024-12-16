import logging
import re
from uuid import uuid4

import aio_pika
import msgpack
from aio_pika import ExchangeType
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from consumer.schema.task import CreateTaskMessage
from db.storage.rabbit import channel_pool
from src.handlers.admin_handlers.state_handlers.router import router
from src.keyboards.admin_kb import admin_complex_kb
from src.states.create_task import CreateTaskState


async def parse_input(value: str):
    if value.isdigit():
        return int(value)
    match = re.fullmatch(r'"([^"]*)"', value)
    if match:
        return match.group(1)
    raise ValueError('Некорректный формат ввода. Используйте число или текст в кавычках.')


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
    await state.update_data(complexity=complexity)
    await callback.message.answer('Сколько будет <b>входных тестов</b>?', parse_mode='HTML')
    await state.set_state(CreateTaskState.waiting_for_input_test_count)


@router.message(CreateTaskState.waiting_for_input_test_count)
async def waiting_for_input_test_count(message: Message, state: FSMContext):
    try:
        input_test_count = int(message.text)
        if input_test_count <= 0:
            raise ValueError('Количество тестов должно быть положительным.')
        await state.update_data(input_test_count=input_test_count, input_tests=[], correct_answers=[])
        await message.answer('Введите <b>входные данные</b> для теста 1', parse_mode='HTML')
        await state.set_state(CreateTaskState.waiting_for_input_test)
    except ValueError:
        await message.answer('Введите корректное число тестов.')


@router.message(CreateTaskState.waiting_for_input_test)
async def waiting_for_input_test(message: Message, state: FSMContext):
    data = await state.get_data()
    input_tests = data.get('input_tests', [])
    try:
        inputs = [item.strip() for item in message.text.split(',')]
        parsed_inputs = [await parse_input(value) for value in inputs]
        input_tests.append(parsed_inputs)
        await state.update_data(input_tests=input_tests)

        if len(input_tests) < data['input_test_count']:
            await message.answer(f'Введите <b>входные данные</b> для теста {len(input_tests) + 1}', parse_mode='HTML')
        else:
            await message.answer('Введите <b>ответ</b> для теста 1', parse_mode='HTML')
            await state.set_state(CreateTaskState.waiting_for_correct_answer)
    except ValueError as e:
        await message.answer(str(e))


@router.message(CreateTaskState.waiting_for_correct_answer)
async def waiting_for_correct_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    correct_answers = data.get('correct_answers', [])
    try:
        parsed_answer = await parse_input(message.text)
        correct_answers.append(parsed_answer)
        await state.update_data(correct_answers=correct_answers)

        if len(correct_answers) < data['input_test_count']:
            await message.answer(f'Введите <b>ответ</b> для теста {len(correct_answers) + 1}', parse_mode='HTML')
        else:
            await message.answer('Сколько будет <b>секретных тестов</b>?', parse_mode='HTML')
            await state.set_state(CreateTaskState.waiting_for_secret_test_count)
    except ValueError as e:
        await message.answer(str(e))


@router.message(CreateTaskState.waiting_for_secret_test_count)
async def waiting_for_secret_test_count(message: Message, state: FSMContext):
    try:
        secret_test_count = int(message.text)
        if secret_test_count <= 0:
            raise ValueError('Количество тестов должно быть положительным.')
        await state.update_data(secret_test_count=secret_test_count, secret_tests=[], secret_answers=[])
        await message.answer('Введите <b>входные данные</b> для секретного теста 1', parse_mode='HTML')
        await state.set_state(CreateTaskState.waiting_for_secret_test)
    except ValueError:
        await message.answer('Введите корректное число тестов.')


@router.message(CreateTaskState.waiting_for_secret_test)
async def waiting_for_secret_test(message: Message, state: FSMContext):
    data = await state.get_data()
    secret_tests = data.get('secret_tests', [])
    try:
        parsed_secret_test = await parse_input(message.text)
        secret_tests.append([parsed_secret_test])
        await state.update_data(secret_tests=secret_tests)

        if len(secret_tests) < data['secret_test_count']:
            await message.answer(
                f'Введите <b>входные данные</b> для секретного теста {len(secret_tests) + 1}',
                parse_mode='HTML',
            )
        else:
            await message.answer('Введите <b>ответ</b> для секретного теста 1', parse_mode='HTML')
            await state.set_state(CreateTaskState.waiting_for_secret_answer)
    except ValueError as e:
        await message.answer(str(e))


@router.message(CreateTaskState.waiting_for_secret_answer)
async def waiting_for_secret_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    secret_answers = data.get('secret_answers', [])
    try:
        parsed_secret_answer = await parse_input(message.text)
        secret_answers.append(parsed_secret_answer)
        await state.update_data(secret_answers=secret_answers)

        if len(secret_answers) < data['secret_test_count']:
            await message.answer(
                f'Введите <b>ответ</b> для секретного теста {len(secret_answers) + 1}',
                parse_mode='HTML',
            )
        else:
            await save_task_to_database(message, state)
    except ValueError as e:
        await message.answer(str(e))


async def save_task_to_database(message: Message, state: FSMContext):
    data = await state.get_data()
    try:
        async with channel_pool.acquire() as channel:  # type: aio_pika.Channel
            exchange = await channel.declare_exchange('user_tasks', ExchangeType.TOPIC, durable=True)
            await exchange.publish(
                aio_pika.Message(
                    msgpack.packb(
                        CreateTaskMessage(
                            id=str(uuid4()),
                            title=data['title'],
                            description=data['description'],
                            complexity=data['complexity'],
                            input_data=data['input_tests'],
                            correct_answer=data['correct_answers'],
                            secret_input=data['secret_tests'],
                            secret_answer=data['secret_answers'],
                            event='tasks',
                            action='create_task',
                        )
                    )
                ),
                routing_key='user_messages',
            )
        await message.answer('Задача успешно сохранена в базу данных.')
    except aio_pika.exceptions.AMQPError as amqp_error:
        await message.answer('Ошибка при работе с RabbitMQ.')
        logging.exception(amqp_error)
    except msgpack.PackValueError as pack_error:
        await message.answer('Ошибка при сериализации данных.')
        logging.exception(pack_error)
    finally:
        await state.clear()
