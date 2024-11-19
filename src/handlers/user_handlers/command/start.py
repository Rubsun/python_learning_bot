from aio_pika import ExchangeType
from aiogram.filters.command import CommandStart
from aiogram.types import Message

from config.settings import settings
from db.storage.rabbit import channel_pool
from src.handlers.user_handlers.command.router import router
from src.keyboards.user_kb import start_kb


@router.message(CommandStart())
async def start_handler(message: Message):

    async with channel_pool.acquire() as channel:  # type: aio_pika.Channel
        exchange = await channel.declare_exchange("user_tasks", ExchangeType.TOPIC, durable=True)

        queue = await channel.declare_queue(
            settings.USER_TASK_QUEUE_TEMPLATE.format(
                user_id=message.from_user.id,
            ),
            durable=True,
        )

        await queue.bind(
            exchange,
            settings.USER_TASK_QUEUE_TEMPLATE.format(
                user_id=message.from_user.id,
            ),
        )

    txt = (
        "Привет! 👋\n\n"
        "<b>Добро пожаловать в нашего бота для изучения Python! 🐍</b>\n\n"
        "Здесь ты сможешь получить задания по программированию, отправить свои решения и узнать, насколько они верны.\n\n"
        "<b>Как это работает?</b>\n"
        "1️⃣ <i>Выбери уровень сложности:</i> легкий, средний или сложный.\n"
        "2️⃣ Получи задачу.\n"
        "3️⃣ Реши её и отправь свой код.\n"
        "4️⃣ Мы проверим твое решение и сразу сообщим, правильно ли оно!\n\n"
        "<b>Готов?</b> Жми «<b>Получить задание</b>» и начинай кодить! 💻✨"
    )

    await message.answer(txt, reply_markup=start_kb, parse_mode='HTML')
