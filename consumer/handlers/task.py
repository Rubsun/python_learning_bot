import logging

import aio_pika
import msgpack
from aio_pika import ExchangeType
from sqlalchemy import select

from config.settings import settings
from consumer.logger import correlation_id_ctx
from consumer.schema.task import TaskMessage, CreateTaskMessage, GetTaskByIdMessage
from consumer.utils import task_to_dict
from db.model.task import Task
from db.storage import rabbit
from db.storage.db import async_session


async def handle_task(message: TaskMessage | CreateTaskMessage | GetTaskByIdMessage):
    async with async_session() as db:
        logging.info(f"handle_task: session ID = {id(db)}")
    if message['action'].startswith('get_tasks_by_complexity'):
        complexity = message['action'].split(':')[1]
        async with async_session() as db:
            not_fetched = await db.execute(select(Task).where(Task.complexity == complexity))
            tasks = not_fetched.scalars().all()

            tasks_as_dicts = [await task_to_dict(task) for task in tasks]

            async with rabbit.channel_pool.acquire() as channel:  # type: aio_pika.Channel
                exchange = await channel.declare_exchange("user_tasks", ExchangeType.TOPIC, durable=True)

                await exchange.publish(
                    aio_pika.Message(
                        msgpack.packb(
                            {
                                'tasks': tasks_as_dicts,
                            }
                        ),
                        correlation_id=correlation_id_ctx.get(),
                    ),
                    routing_key=settings.USER_TASK_QUEUE_TEMPLATE.format(user_id=message['user_id']),
                )

    elif message['action'] == 'create_task':
        try:
            task = Task(
                title=message['title'],
                description=message['description'],
                complexity=message['complexity'],
                input_data=list(message['input_data']),
                secret_input=list(message['secret_input']),
                correct_answer=list(message['correct_answer']),
                secret_answer=list(message['secret_answer']),
            )
            async with async_session() as db:
                db.add(task)
                await db.commit()
        except Exception as e:
            print(e)
    elif message['action'] == 'get_task_by_id':
        async with async_session() as db:
            taskq = await db.scalar(select(Task).where(Task.id == message['task_id']))
        task = await task_to_dict(taskq)
        async with rabbit.channel_pool.acquire() as channel:  # type: aio_pika.Channel
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
