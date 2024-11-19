from aio_pika import ExchangeType

from db.storage.rabbit import channel_pool


async def init_rabbitmq():
    async with channel_pool.acquire() as channel:
        exchange = await channel.declare_exchange("user_tasks", ExchangeType.TOPIC, durable=True)
        queue = await channel.declare_queue('user_messages', durable=True)
        await queue.bind(exchange, 'user_messages')
