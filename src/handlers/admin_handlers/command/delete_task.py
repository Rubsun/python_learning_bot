import aio_pika
import msgpack
from aio_pika import ExchangeType
from aiogram import F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from router import router

from consumer.schema.task import TaskMessage
from db.storage.rabbit import channel_pool
from src.keyboards.user_kb import complex_kb


@router.message(Command('delete_task'))
async def delete_task(message: Message):
    await message.answer('Выберите сложность задачи, которую хотите удалить', reply_markup=complex_kb)


@router.callback_query(F.data.startswith('complexity_'))
async def get_complexity(callback: CallbackQuery):
    complexity = callback.data.split('_')[-1]
    async with channel_pool.acquire() as channel:
        exchange = await channel.declare_exchange('user_tasks', ExchangeType.TOPIC, durable=True)

        await exchange.publish(
            aio_pika.Message(
                msgpack.packb(
                    TaskMessage(
                        user_id=callback.from_user.id, action=f'get_tasks_by_complexity:{complexity}', event='tasks'
                    )
                ),
            ),
            'user_messages',
        )
