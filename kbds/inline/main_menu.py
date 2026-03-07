from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from database.Orders import orm_get_orders_by_status


class MenuCallBackAdmin(CallbackData, prefix="admin_menu"):
    level: int
    menu_name: str
    category_id: int | None = None
    banner_id: int | None = None
    service_id: int | None = None
    page: int | None = 1


class MenuCallBack(CallbackData, prefix="menu"):
    level: int
    menu_name: str
    category: int | None = None
    page: int | None = 1
    service_id: int | None = None
    date: str | None = None


async def get_client_main_btns(
        *,
        level: int,
        sizes: tuple[int] = (2,),
        state = None
):
    
    if state is not None:
        data = await state.get_data()
        cart_services = [int(i) for i in data.get("list_services", [])]
    else:
        cart_services = []
    total_len = len(cart_services)
    count_services = f" ({total_len} шт.)" if total_len > 0 else ""
    text_basket = f"🛒 Корзина {count_services}"


    keyboard = InlineKeyboardBuilder()
    btns = {
        "📂 Каталог": "catalog",
        text_basket: "order",
        "ℹ️ О нас": "about",
        "💳 Оплата": "payment",
    }
    for text, menu_name in btns.items():
        if menu_name == 'catalog':
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCallBack(level=level+1, menu_name=menu_name).pack()))

        elif menu_name == 'order':
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCallBack(level=3, menu_name=menu_name).pack()))

        else:
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCallBack(level=level, menu_name=menu_name).pack()))
    return keyboard.adjust(*sizes).as_markup()


def get_admin_main_btns(
        *,
        level: int,
        sizes: tuple[int] = (2,),
):
    keyboard = InlineKeyboardBuilder()
    btns = {
        "⚙️ Настройки": "settings",
        "Записи": "order",
        "Выход": "exit",

    }
    for text, menu_name in btns.items():
        if menu_name == 'settings':
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCallBackAdmin(level=level+1, menu_name=menu_name).pack()))

        elif menu_name == 'order':
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCallBackAdmin(level=3, menu_name=menu_name).pack()))

        else:
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCallBackAdmin(level=level, menu_name=menu_name).pack()))
    return keyboard.adjust(*sizes).as_markup()
