from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton


def get_callback_btns(
        *,
        btns: dict[str, str],
        sizes: tuple[int] = (2,),
):
    builder = InlineKeyboardBuilder()

    for text, data in btns.items():
        builder.add(InlineKeyboardButton(text=text, callback_data=data))

    # При нажатии вернет callback_data
    return builder.adjust(*sizes).as_markup()


def get_url_btns(
    *,
    btns: dict[str, str],
    sizes: tuple[int] = (2,)
):
    builder = InlineKeyboardBuilder()

    for text, url in btns.items():
        builder.add(InlineKeyboardButton(text=text, url=url))

    builder.adjust(*sizes)
    return builder.as_markup()  # При нажатии вернет url


def get_inlineMix_btns(
    *,
    btns: dict[str, str],
    sizes: tuple[int] = (2,)
):
    builder = InlineKeyboardBuilder()

    for text, value in btns.items():
        if '://' in value:
            builder.add(InlineKeyboardButton(text=text, url=value))
        else:
            builder.add(InlineKeyboardButton(text=text, callback_data=value))

    builder.adjust(*sizes)
    return builder.as_markup()  # При нажатии вернет url


button_categories_admin = get_callback_btns(btns={
    'Список категорий': 'categories_list',
    'Добавить категорию': 'add_category',
    'Назад': 'prev_settings'
})

buttons_start_admin = get_callback_btns(btns={
    'Запись': 'recording',
    'Настройки': 'settings',
    'Выйти': 'exit',
})

button_settings_admin = get_callback_btns(btns={
    'Категории': 'categories',
    'Баннеры': 'banners',
    'Записи': 'recording',
    'Назад': 'prev_menu'
})

button_service_admin = get_callback_btns(btns={
    'Добавить Услугу': 'add_service',
    'Назад': 'prev_category'
})

button_banner_admin = get_callback_btns(btns={
    'Список баннеров': 'banners_list',
    # 'Добавить Баннеры': 'add_banners',
    'Назад': 'prev_category'
})
