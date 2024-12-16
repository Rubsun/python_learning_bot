from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

admin_complex_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Сложнаяaa 😈', callback_data='admin_complexity_hard')],
        [InlineKeyboardButton(text='Средняя 👹', callback_data='admin_complexity_normal')],
        [InlineKeyboardButton(text='Легкая 😇', callback_data='admin_complexity_easy')],
    ]
)
