from aiogram import types
from aiogram.types import InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.context import FSMContext


from database.Orders import orm_get_orders_by_status
from database.Paginator import Paginator, pages
from database.Banner import orm_get_banner
from database.Category import orm_get_categories_inner_join_services
from handlers.private_chat.query_users.Order import order_menu
from handlers.private_chat.query_users.Service import services_menu
from kbds.inline.main_menu import MenuCallBack, get_client_main_btns
from kbds.inline.inline import get_user_catalog_btns


async def check_image_for_menu(
    message: types.Message,
    session: AsyncSession,
    state: FSMContext,
    menu_name: str = "main",
    client_id: int | None = None,
):
    if client_id is None:
        client_id = message.from_user.id

    # 1. Получаем текущие заказы из БД ОДИН РАЗ
    orders = await orm_get_orders_by_status(session, client_id, status_id=1)
    
    # 2. Формируем актуальный список услуг из БД
    db_services = []
    if orders:
        for order in orders:
            for item in order.items:
                db_services.extend([int(item.service_id)] * item.quantity)

    # 3. Синхронизируем FSM
    data = await state.get_data()
    cart_services = [int(i) for i in data.get("list_services", [])]

    if cart_services != db_services:
        print(f"Синхронизация FSM с БД для пользователя {client_id}")
        await state.update_data(list_services=db_services)

    # 4. Получаем контент меню
    media, replay_markup = await get_menu_content(
        session, level=0, menu_name=menu_name, client_id=client_id, state=state
    )

    # 5. Отправка пользователю
    if isinstance(media, types.InputMediaPhoto):
        await message.answer_photo(
            photo=media.media,
            caption=media.caption,
            reply_markup=replay_markup,
            parse_mode="HTML"
        )
    else:
        # Если баннер не найден или это текст
        caption = media.description if hasattr(media, 'description') else "Меню"
        await message.answer(
            text=caption,
            reply_markup=replay_markup,
            parse_mode="HTML"
        )


async def main_menu(session, level, menu_name, state=None, client_id=None):

    banner = await orm_get_banner(session, menu_name)
    kbds = await get_client_main_btns(level=level, state=state)

    if not banner.image:
        return banner, kbds

    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    return image, kbds


async def catalog_menu(session, level, menu_name, state=None):
    banner = await orm_get_banner(session=session, page=menu_name)
    categories = await orm_get_categories_inner_join_services(session=session)

    kbds = await get_user_catalog_btns(
        level=level, categories=categories, state=state)

    if not banner.image:
        return banner, kbds

    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    return image, kbds


async def get_menu_content(
        session: AsyncSession,
        level: int,
        menu_name: str,
        category: int | None = None,
        page: int | None = None,
        state: FSMContext | None = None,
        client_id: int | None = None
):

    if level == 0:
        return await main_menu(session, level, menu_name, state=state)
    elif level == 1:
        return await catalog_menu(session, level, menu_name, state=state)
    elif level == 2:
        return await services_menu(session, level, category, page, state=state)
    elif level == 3:
        return await order_menu(session, level, menu_name, state, client_id)
