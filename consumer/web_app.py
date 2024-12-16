import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from consumer.api.tech.router import router as tech_router
from consumer.app import start_consumer
from consumer.logger import LOGGING_CONFIG, logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logging.config.dictConfig(LOGGING_CONFIG)

    logger.info('Starting lifespan')
    task = asyncio.create_task(start_consumer())
    logger.info('Started succesfully')
    yield
    task.cancel()
    logger.info('Ending lifespan')


def create_app() -> FastAPI:
    app = FastAPI(docs_url='/swagger', lifespan=lifespan)
    app.include_router(tech_router, prefix='', tags=['tech'])
    return app
