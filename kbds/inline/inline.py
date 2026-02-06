from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton


from kbds.inline.main_menu_client import MenuCallBack


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


def get_user_catalog_btns(*, level: int, categories: list, sizes: tuple[int] = (2,),):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='Назад', callback_data=MenuCallBack(
        level=level-1, menu_name='main').pack()))
    keyboard.add(InlineKeyboardButton(
        text='Корзина', callback_data=MenuCallBack(level=3, menu_name='order').pack()))

    if not categories:
        return keyboard.adjust(*sizes).as_markup()

    for cat in categories:
        keyboard.add(InlineKeyboardButton(text=cat.name, callback_data=MenuCallBack(
            level=level+1, menu_name=cat.name, category=cat.id).pack()))

    return keyboard.adjust(*sizes).as_markup()


def get_products_btns(
    *,
    level: int,
    category: int,
    page: int,
    pagination_btns: dict,
    product_id: int,
    sizes: tuple[int] = (2, 1)
):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='Назад', callback_data=MenuCallBack(
        level=level-1, menu_name='catalog').pack()))
    keyboard.add(InlineKeyboardButton(
        text='Корзина', callback_data=MenuCallBack(level=3, menu_name='order').pack()))
    keyboard.add(InlineKeyboardButton(text='Выбрать', callback_data=MenuCallBack(
        level=level, menu_name='add_to_order', product_id=product_id).pack()))

    keyboard.adjust(*sizes)

    row = []

    for text, menu_name in pagination_btns.items():
        if menu_name == "next":
            row.append(InlineKeyboardButton(text=text, callback_data=MenuCallBack(
                level=level, menu_name=menu_name, category=category, page=page + 1).pack()))
        elif menu_name == "prev":
            row.append(InlineKeyboardButton(text=text, callback_data=MenuCallBack(level=level, menu_name=menu_name, category=category, page=page - 1).pack()))\

    return keyboard.row(*row).as_markup()


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
    'Запись': 'orders',
    'Настройки': 'settings',
    'Выйти': 'exit',
})

button_settings_admin = get_callback_btns(btns={
    'Категории': 'categories',
    'Баннеры': 'banners',
    'Расписание': 'recording',
    'Назад': 'prev_menu'
})

button_service_admin = get_callback_btns(btns={
    'Добавить Услугу': 'add_service',
    'Назад': 'prev_category'
})

button_banner_admin = get_callback_btns(btns={
    'Список баннеров': 'banners_list',
    # 'Добавить Баннеры': 'add_banners',
    'Назад': 'prev_settings'
})
