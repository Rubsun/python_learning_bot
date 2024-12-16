import asyncio
import json
import logging
from pathlib import Path

from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from consumer.utils import task_to_dict
from db.model import meta
from db.model.task import Task


async def load_fixture(files: list[Path], session: AsyncSession) -> None:
    try:
        for file in files:
            with open(file, 'r') as f:
                table = meta.metadata.tables[file.stem]
                await session.execute(insert(table).values(json.load(f)))
        await session.commit()  # Важно!
    except Exception as e:
        logging.error(e)
        await session.rollback()
    not_fetched = await session.execute(select(Task).where(Task.complexity == 'hard'))
    tasks = not_fetched.scalars().all()

    tasks_as_dicts = [await task_to_dict(task) for task in tasks]
    print(tasks_as_dicts)


if __name__ == '__main__':
    asyncio.run(
        main(
            [
                Path('fixtures/public.gift.json'),
            ]
        )
    )
