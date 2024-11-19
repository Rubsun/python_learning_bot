from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

start_kb = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text='Получить задание', callback_data='get_complexity')]]
)

complex_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Сложная 😈', callback_data='complexity_hard')],
        [InlineKeyboardButton(text='Средняя 👹', callback_data='complexity_normal')],
        [InlineKeyboardButton(text='Легкая 😇', callback_data='complexity_easy')],
    ]
)


async def generate_carousel_keyboard(items, callback_prefix, page=0, page_size=6):
    keyboard_buttons = []
    start_index = page * page_size
    end_index = start_index + page_size
    current_items = items[start_index:end_index]
    for item in current_items:
        button = InlineKeyboardButton(text=item['title'], callback_data=f"{callback_prefix}:{item['id']}")
        keyboard_buttons.append([button])

    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(
            InlineKeyboardButton(text='⬅️ Назад', callback_data=f"{callback_prefix}:prev:{page - 1}")
        )
    if end_index < len(items):
        navigation_buttons.append(
            InlineKeyboardButton(text='➡️ Вперед', callback_data=f"{callback_prefix}:next:{page + 1}")
        )

    if navigation_buttons:
        keyboard_buttons.append(navigation_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
