import aio_pika
import msgpack
import asyncio
import time
from aio_pika import ExchangeType
from sqlalchemy import select

from consumer.metrics_init import DB_FETCH_REQUESTS, DB_FETCH_PROCESSING_TIME
from config.settings import settings
from consumer.logger import correlation_id_ctx
from consumer.schema.task import TaskMessage, CreateTaskMessage, GetTaskByIdMessage
from consumer.utils import task_to_dict
from db.model.task import Task
from db.storage.db import async_session
from db.storage.rabbit import channel_pool
from src.api.tech.metrics import metrics


async def handle_task(message: TaskMessage | CreateTaskMessage | GetTaskByIdMessage):
    if message['action'].startswith('get_tasks_by_complexity'):
        print(message)

        complexity = message['action'].split(':')[1]

        async with async_session() as db:
            DB_FETCH_REQUESTS.inc()
            start_time = time.monotonic()

            not_fetched = await db.execute(select(Task).where(Task.complexity == complexity))
            tasks = not_fetched.scalars().all()

            DB_FETCH_PROCESSING_TIME.observe(time.monotonic() - start_time)

            tasks_as_dicts = [await task_to_dict(task) for task in tasks]

            async with channel_pool.acquire() as channel:  # type: aio_pika.Channel
                exchange = await channel.declare_exchange("user_tasks", ExchangeType.TOPIC, durable=True)

                await exchange.publish(
                    aio_pika.Message(
                        msgpack.packb({
                            'tasks': tasks_as_dicts,
                        }),
                        correlation_id=correlation_id_ctx.get(),
                    ),
                    routing_key=settings.USER_TASK_QUEUE_TEMPLATE.format(user_id=message['user_id']),
                )

    elif message['action'] == 'create_task':
        async with async_session() as db:
            task = Task(
                title=message['title'],
                description=message['description'],
                complexity=message['complexity'],
                input_data=message['input_data'],
                correct_answer=message['correct_answer'],
                secret_answer=message['secret_answer'],
            )
            db.add(task)
            db.commit()

    elif message['action'] == 'get_task_by_id':
        async with async_session() as db:
            DB_FETCH_REQUESTS.inc()
            start_time = time.monotonic()

            taskq = await db.scalar(select(Task).where(Task.id == message['task_id']))

            DB_FETCH_PROCESSING_TIME.observe(time.monotonic() - start_time)

        task = await task_to_dict(taskq)
        async with channel_pool.acquire() as channel:  # type: aio_pika.Channel
            exchange = await channel.declare_exchange("user_tasks", ExchangeType.TOPIC, durable=True)

            await exchange.publish(
                aio_pika.Message(
                    msgpack.packb(
                        {
                            'task': task,
                        }
                    ),
                    correlation_id=correlation_id_ctx.get(),
                ),
                routing_key=settings.USER_TASK_QUEUE_TEMPLATE.format(user_id=message['user_id']),
            )
