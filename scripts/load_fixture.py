import json
import logging
from pathlib import Path

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from db.model import meta


async def load_fixture(files: list[Path], session: AsyncSession) -> None:
    try:
        for file in files:
            with open(file, 'r') as f:
                table = meta.metadata.tables[file.stem]
                await session.execute(insert(table).values(json.load(f)))
        await session.commit()
    except Exception as e: # noqa
        logging.error(e)
    await session.rollback()
