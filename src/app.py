import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

import uvicorn
from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.redis import RedisStorage
from fastapi import FastAPI
from starlette_context import plugins
from starlette_context.middleware import RawContextMiddleware

from config.settings import settings
from db.storage.db import async_session
from db.storage.redis import setup_redis
from src.api.tg.router import router as tg_router
from src.bg_task import background_tasks
from src.bot import setup_bot, setup_dp
from src.handlers.admin_handlers.command.router import router as admin_cmd_router
from src.handlers.admin_handlers.state_handlers.router import router as admin_state_router
from src.handlers.user_handlers.callback.router import router as user_callback_router
from src.handlers.user_handlers.command.router import router as user_command_start_router
from src.handlers.user_handlers.state_handlers.router import router as user_state_router
from src.api.tech.router import router as tech_router
from src.logger import LOGGING_CONFIG, logger
from src.middlewares.rps_middleware import RequestCountMiddleware
from src.rabbit_initializer import init_rabbitmq


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logging.config.dictConfig(LOGGING_CONFIG)
    logger.info('Starting lifespan')
    redis = setup_redis()
    storage = RedisStorage(redis=redis)
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=storage)
    setup_bot(bot)
    setup_dp(dp)
    dp.include_router(admin_cmd_router)
    dp.include_router(admin_state_router)
    dp.include_router(user_callback_router)
    dp.include_router(user_command_start_router)
    dp.include_router(user_state_router)

    await init_rabbitmq()
    await bot.set_webhook(settings.BOT_WEBHOOK_URL)

    temp = await bot.get_webhook_info()
    logger.info(f'WEBHOOK: {temp}')
    logger.info('Finished start')
    yield

    start_time = time.monotonic()
    is_used = False
    while background_tasks:
        if (time.monotonic() - start_time) / 3600 > 0.5 and not is_used:
            logger.warning('Background tasks has expired for more than 30 seconds')
            is_used = True

        await asyncio.sleep(0)

    if background_tasks:
        logger.warning('not all background tasks are done')

    logger.info('closed background tasks...')
    logger.info(f'[{datetime.now()}]  background tasks: {[i for i in background_tasks]}')
    await bot.delete_webhook()
    logger.info('delete webhook...')
    temp = await bot.get_webhook_info()
    logger.info(f'WEBHOOK: {temp}')
    logger.info('Ending lifespan')


def create_app() -> FastAPI:
    app = FastAPI(docs_url='/swagger', lifespan=lifespan)
    app.include_router(tg_router, prefix='/tg', tags=['tg'])
    app.include_router(tech_router, prefix='/tech', tags=['tech'])
    app.middleware("http")(RequestCountMiddleware())
    app.add_middleware(RawContextMiddleware, plugins=[plugins.CorrelationIdPlugin()])
    return app


async def start_polling():
    logging.config.dictConfig(LOGGING_CONFIG)
    logger.info('Starting polling')
    redis = setup_redis()
    storage = RedisStorage(redis=redis)
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=storage)
    setup_dp(dp)
    setup_bot(bot)
    dp.include_router(admin_cmd_router)
    dp.include_router(admin_state_router)
    dp.include_router(user_callback_router)
    dp.include_router(user_command_start_router)
    dp.include_router(user_state_router)
    await bot.delete_webhook()
    await init_rabbitmq()

    logger.info('Dependencies launched')
    await dp.start_polling(bot, dp=async_session)


if __name__ == '__main__':
    if settings.BOT_WEBHOOK_URL:
        uvicorn.run('src.app:create_app', factory=True, host='0.0.0.0', port=8001, workers=1)
    else:
        asyncio.run(start_polling())
