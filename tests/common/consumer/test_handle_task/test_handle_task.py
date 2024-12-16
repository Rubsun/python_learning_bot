import uuid
from pathlib import Path

import aio_pika
import msgpack
import pytest
from sqlalchemy import select

from config.settings import settings
from consumer.app import start_consumer
from consumer.schema.task import TaskMessage
from consumer.utils import task_to_dict
from db.model.task import Task
from tests.mocking.rabbit import MockExchange

BASE_DIR = Path(__file__).parent
SEED_DIR = BASE_DIR / 'seeds'


@pytest.mark.parametrize(
    ('predefined_queue', 'seeds', 'correlation_id'),
    [
        (
            TaskMessage(user_id=1, action=f'get_tasks_by_complexity:hard', event='tasks'),
            [SEED_DIR / 'public.task.json'],
            str(uuid.uuid4()),
        )
    ],
)
@pytest.mark.asyncio
@pytest.mark.usefixtures('_load_queue', '_load_seeds')
async def test_handle_task(db_session, predefined_queue, correlation_id, mock_exchange: MockExchange, seeds):
    await start_consumer()
    expected_routing_key = settings.USER_TASK_QUEUE_TEMPLATE.format(user_id=predefined_queue['user_id'])
    expected_calls = []

    async with db_session:
        not_fetched = await db_session.execute(select(Task).where(Task.complexity == 'hard'))
        tasks = not_fetched.scalars().all()
        tasks_as_dicts = [await task_to_dict(task) for task in tasks]

        expected_message = aio_pika.Message(
            msgpack.packb(
                {
                    'tasks': tasks_as_dicts,
                }
            ),
            correlation_id=correlation_id,
        )
        expected_calls.append(('publish', (expected_message,), {'routing_key': expected_routing_key}))

    mock_exchange.assert_has_calls(expected_calls, any_order=True)
