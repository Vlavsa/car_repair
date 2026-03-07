from aiogram import Router, types
from aiogram.types import InputMediaPhoto
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


from sqlalchemy.ext.asyncio import AsyncSession


from kbds.inline.main_menu import MenuCallBack
from database.Paginator import Paginator, pages
from database.Banner import orm_get_banner
from database.Orders import orm_get_orders_by_status


order_for_user_router = Router()


async def order_menu(session, level, menu_name, client_id, category, page, state):
    status_id = 1
    kb_builder = InlineKeyboardBuilder()

    kb_builder.add(InlineKeyboardButton(text="🔙 Меню", callback_data=MenuCallBack(
        level=0, menu_name="main", category=category, page=page).pack()))

    banner = await orm_get_banner(session, page="order")
    orders = await orm_get_orders_by_status(
        session=session, client_id=client_id, status_id=status_id)

    caption = f"Корзина{' пуста' if not orders else ':'}"

    if not banner or not banner.image:
        image = caption

    else:
        image = InputMediaPhoto(
            media=banner.image,
            caption=caption,
            parse_mode="HTML"
        )

    if not orders:
        return image, kb_builder.as_markup()

    kb = await get_order_btns(state=state)

    return image, kb_builder.as_markup()


async def get_order_btns(
    *,
    level: int,
    page: int,
    sizes: tuple[int] = (2, 1),
    state=None,
):

    ...


@order_for_user_router.callback_query(MenuCallBack.filter(F.menu_name == "add_to_order"))
async def add_an_order_with_services(session: AsyncSession, callback: types.CallbackQuery, callback_data: MenuCallBack, state: FSMContext):

    if state is not None:
        data = await state.get_data()

        cart_services = [int(i) for i in data.get("list_services", [])]
    else:
        cart_services = []

    # callback_data = level=level, menu_name=menu_action, category=category, service_id=service_id, page=page