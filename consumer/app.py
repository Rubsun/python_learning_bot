import logging.config

import msgpack

from consumer.handlers.task import handle_task
from consumer.logger import LOGGING_CONFIG, correlation_id_ctx, logger
from consumer.metrics_init import REQUESTS
from consumer.schema.task import TaskMessage
from db.storage import rabbit


async def start_consumer() -> None:
    logging.config.dictConfig(LOGGING_CONFIG)
    logger.info('Starting consumer...')

    queue_name = 'user_messages'

    async with rabbit.channel_pool.acquire() as channel:

        await channel.set_qos(prefetch_count=10)

        queue = await channel.declare_queue(queue_name, durable=True)
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                REQUESTS.inc()
                async with message.process():
                    correlation_id_ctx.set(message.correlation_id)
                    body: TaskMessage = msgpack.unpackb(message.body)
                    if body['event'] == 'tasks':
                        logging.info(body['event'])
                        logging.info(body['action'])
                        await handle_task(body)
