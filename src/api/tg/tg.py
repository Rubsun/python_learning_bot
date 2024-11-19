from aiogram.types import Update
from fastapi.requests import Request

from src.api.tg.router import router
from src.bot import get_bot, get_dp


@router.post("/webhook")
async def webhook(request: Request) -> None:
    bot = get_bot()
    dp = get_dp()
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
