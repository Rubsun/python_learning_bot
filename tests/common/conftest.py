from collections import deque
from pathlib import Path
from typing import Any, AsyncGenerator

import aio_pika
import msgpack
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from db.storage import rabbit, rabbit as consumer_rabbit
from db.storage.db import async_session, get_db
from scripts.load_fixture import load_fixture
from src.app import create_app
from tests.mocking.rabbit import MockChannel, MockChannelPool, MockExchange, MockExchangeMessage, MockQueue

BASE_DIR = Path(__file__).parent
SEED_DIR = BASE_DIR / 'seeds'


@pytest.fixture(scope='session')
def app() -> FastAPI:
    return create_app()


@pytest_asyncio.fixture()
async def db_session(app: FastAPI) -> AsyncSession:
    async with async_session() as session:

        async def overrided_db_session() -> AsyncGenerator[AsyncSession, None]:
            yield session
            await session.rollback()

        app.dependency_overrides[get_db] = overrided_db_session
        yield session
        await session.rollback()


@pytest_asyncio.fixture()
async def _load_seeds(db_session: AsyncSession, seeds: list[Path]) -> None:
    await load_fixture(seeds, db_session)


@pytest.fixture
def mock_exchange() -> MockExchange:
    return MockExchange()


@pytest_asyncio.fixture()
async def _load_queue(
    monkeypatch: pytest.MonkeyPatch,
    predefined_queue: Any,
    correlation_id,
    mock_exchange: MockExchange,
):
    queue = MockQueue(deque())

    if predefined_queue is not None:
        await queue.put(msgpack.packb(predefined_queue), correlation_id)

    channel = MockChannel(queue=queue, exchange=mock_exchange)
    pool = MockChannelPool(channel=channel)
    monkeypatch.setattr(rabbit, 'channel_pool', pool)
    monkeypatch.setattr(consumer_rabbit, 'channel_pool', pool)
    monkeypatch.setattr(aio_pika, 'Message', MockExchangeMessage)
