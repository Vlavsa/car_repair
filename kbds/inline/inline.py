from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton


from kbds.inline.main_menu import MenuCallBack


def get_callback_btns(
        *,
        btns: dict[str, str],
        sizes: tuple[int] = (2,),
):
    builder = InlineKeyboardBuilder()

    for text, data in btns.items():
        builder.add(InlineKeyboardButton(text=text, callback_data=data))


    return builder.adjust(*sizes).as_markup()


async def get_user_catalog_btns(*, level: int, categories: list, sizes: tuple[int] = (2,), state=None):

    if state is not None:
        data = await state.get_data()
        cart_services = [int(i) for i in data.get("list_services", [])]
    else:
        cart_services = []
    total_len = len(cart_services)
    count_services = f" ({total_len} шт.)" if total_len > 0 else ""
    text_basket = f"🛒 Корзина {count_services}"

    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='🔙 Назад', callback_data=MenuCallBack(
        level=level-1, menu_name='main').pack()))
    keyboard.add(InlineKeyboardButton(
        text=text_basket, callback_data=MenuCallBack(level=3, menu_name='order').pack()))

    if not categories:
        return keyboard.adjust(*sizes).as_markup()

    for cat in categories:
        keyboard.add(InlineKeyboardButton(text=cat.name, callback_data=MenuCallBack(
            level=level+1, menu_name=cat.name, category=cat.id).pack()))

    return keyboard.adjust(*sizes).as_markup()


def get_url_btns(
    *,
    btns: dict[str, str],
    sizes: tuple[int] = (2,)
):
    builder = InlineKeyboardBuilder()

    for text, url in btns.items():
        builder.add(InlineKeyboardButton(text=text, url=url))

    builder.adjust(*sizes)
    return builder.as_markup()  


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
    return builder.as_markup()
