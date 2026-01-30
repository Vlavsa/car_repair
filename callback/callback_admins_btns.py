from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton


class CategoryClick(CallbackData, prefix="cat"):
    action: str     # "view", "delete", "prev", "next"
    category_id: int = 0
    page: int = 0


def get_paginated_categories_kb(
        categories_data,
        page: int,
        limit: int = 5
):
    builder = InlineKeyboardBuilder()

    start = limit * page
    end = start+limit

    current_pag_data = categories_data[start:end]

    for row in current_pag_data:
        category, count = row
        builder.button(text=f"{category.name} ({count})", callback_data=CategoryClick(
            action="select", category_id=category.id, page=page))

    builder.adjust(3,)  # Категории в столбик

    # Кнопки навигации (в ряд)
    nav_buttons = []
    if page > 0:
        nav_buttons.append(builder.button(
            text="⬅️", callback_data=CategoryClick(action="prev", page=page - 1)
        ))
    if end < len(categories_data):
        nav_buttons.append(builder.button(
            text="➡️", callback_data=CategoryClick(action="next", page=page + 1)
        ))

    return builder.as_markup()
