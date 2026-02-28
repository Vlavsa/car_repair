from aiogram import types
from aiogram.types import InputMediaPhoto
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


from kbds.inline.main_menu import MenuCallBack


from database.Paginator import Paginator, pages
from database.Service import orm_get_services_by_category_id


async def services_menu(session, level, category, page, state=None):
    services = await orm_get_services_by_category_id(session=session, category_id=category)

    if not services:
        kb = InlineKeyboardBuilder()
        kb.row(types.InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=MenuCallBack(level=level-1, menu_name="category").pack())
        )
        return "📂 В этой категории пока нет товаров", kb.as_markup()

    paginator = Paginator(services, page)
    if page > paginator.pages:
        page = paginator.pages
    elif page < 1:
        page = 1

    paginator = Paginator(services, page)

    service = paginator.get_page()[0]

    caption = (
        f"🛠 <b>{service.name}</b>\n"
        f"--------------------\n" 
        f"{service.description}\n\n"
        f"💰 Стоимость: <b>{round(service.price, 2)} ₽</b>\n"
        f"📦 Услуга {paginator.page} из {paginator.pages}"
    )
    image = InputMediaPhoto(
        media=service.image,
        caption=caption,
        parse_mode="HTML"
    )

    pagination_btns = pages(paginator)


    kbds = await get_service_btns(  
        level=level,
        category=category,
        page=page,
        pagination_btns=pagination_btns,
        service_id=service.id,
        state=state
    )

    return image, kbds


async def get_service_btns(
    *,
    level: int,
    category: int,
    page: int,
    pagination_btns: dict,
    service_id: int,
    sizes: tuple[int] = (2, 1),
    state=None,  
):





    if state is not None:
        data = await state.get_data()

        cart_services = [int(i) for i in data.get("list_services", [])]
    else:
        cart_services = []

    total_len = len(cart_services)
    count_services = f" ({total_len} шт.)" if total_len > 0 else ""

    service_id = int(service_id)
    select_text = "✅ Выбрать" if cart_services.count(service_id) == 0  else "✅ Добавить"
    remuved_text = f"❌ Убрать"
    menu_action = "add_to_order"
    reduce_order = "reduce_from_order"
    



    keyboard = InlineKeyboardBuilder()



    keyboard.add(
        InlineKeyboardButton(text='🔙 Назад', callback_data=MenuCallBack(
            level=level-1, menu_name='catalog', category=category).pack()),
        InlineKeyboardButton(text=f'🛒 Корзина {count_services}', callback_data=MenuCallBack(
            level=3, menu_name='order').pack()),
        InlineKeyboardButton(text=select_text, callback_data=MenuCallBack(
            level=level, menu_name=menu_action, category=category, service_id=service_id, page=page).pack())
    )
    if service_id in cart_services:
        keyboard.add(
            InlineKeyboardButton(text=f"{remuved_text} {cart_services.count(service_id)} шт.", callback_data=MenuCallBack(
                level=level, menu_name=reduce_order, category=category, service_id=service_id, page=page).pack())
        )

    keyboard.adjust(*sizes)

    row = []
    for text, name in pagination_btns.items():
        page_num = page + 1 if name == "next" else page - 1
        row.append(InlineKeyboardButton(text=text, callback_data=MenuCallBack(
            level=level, menu_name="service", category=category, page=page_num).pack()))

    return keyboard.row(*row).as_markup()
