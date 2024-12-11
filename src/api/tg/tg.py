import asyncio
from asyncio import Task
from typing import Any

import time
from aiogram.methods.base import TelegramMethod
from aiogram.types import Update
from fastapi.responses import ORJSONResponse
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.bot import get_bot, get_dp
from src.logger import logger
from src.api.tg.router import router
from src.bg_task import background_tasks
from src import bot


@router.post("/webhook")
async def webhook(request: Request) -> JSONResponse:
    update = await request.json()
    task: Task[TelegramMethod[Any] | None] = asyncio.create_task(bot.dp.feed_webhook_update(bot.bot, update))
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)

    return ORJSONResponse({"status": "ok"})
