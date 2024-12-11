import logging.config

import aio_pika
import msgpack

from consumer.handlers.task import handle_task
from consumer.logger import LOGGING_CONFIG, logger, correlation_id_ctx
from consumer.metrics_init import REQUESTS
from consumer.schema.task import TaskMessage
from db.storage.rabbit import channel_pool


async def start_consumer() -> None:
    logging.config.dictConfig(LOGGING_CONFIG)
    logger.info('Starting consumer...')

    queue_name = "user_messages"

    async with channel_pool.acquire() as channel:  # type: aio_pika.Channel

        await channel.set_qos(prefetch_count=10)

        queue = await channel.declare_queue(queue_name, durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                REQUESTS.inc()
                async with message.process():
                    correlation_id_ctx.set(message.correlation_id)
                    logger.info(f"Message ...")
                    body: TaskMessage = msgpack.unpackb(message.body)
                    if body['event'] == 'tasks':
                        logging.info(body['event'])
                        logging.info(body['action'])
                        await handle_task(body)
