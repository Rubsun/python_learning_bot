import asyncio
import logging

from sqlalchemy.exc import IntegrityError

from db.model import meta
from db.storage.db import engine


async def migrate() -> None:
    try:
        async with engine.begin() as conn:
            await conn.run_sync(meta.metadata.create_all)
    except IntegrityError:
        logging.exception('Already exists')


if __name__ == '__main__':
    asyncio.run(migrate())
