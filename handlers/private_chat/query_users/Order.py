from aiogram import F, Router, types

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto
from aiogram.types import InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


from database.Client import orm_check_client
from database.Orders import orm_add_to_order, orm_delete_from_order
from filters.chat_types import ChatTypeFilter
from handlers.private_chat.query_users.Service import services_menu
from handlers.private_chat.query_users.menu_processing import check_image_for_menu
from handlers.private_chat.query_users.state import AddClient
from kbds.inline.main_menu import MenuCallBack


from database.Paginator import Paginator, pages


order_user_router = Router()
order_user_router.message.filter(ChatTypeFilter(["private"]))


@order_user_router.callback_query(MenuCallBack.filter(F.menu_name == "add_to_order"))
async def add_to_order(callback: types.CallbackQuery, state: FSMContext, callback_data: MenuCallBack, session: AsyncSession):
    print()
    
    
    user_tg_id = callback.from_user.id
    user = await orm_check_client(session=session, client_id=user_tg_id)

    data = await state.get_data()
    service_id = callback_data.service_id
    list_services = data.get("list_services", [])
    print(f"list_services: {list_services}")
    if list_services.count(service_id) >= 10:
        return await callback.answer("⚠️ Максимальное количество для этой услуги (10 шт.)", show_alert=True)

    list_services.append(service_id)

    if user:

        await orm_add_to_order(
            session=session,
            client_id=user_tg_id,
            service_id=service_id,
            status_id=1
        )
        await state.update_data(list_services=list_services)

        image, kbds = await services_menu(
            session=session,
            level=callback_data.level,
            category=callback_data.category,
            page=callback_data.page,
            state=state
        )

        try:
            await callback.message.edit_media(media=image, reply_markup=kbds)
        except Exception:
            pass

        await callback.answer("Добавлено ✅")
        return

    else:

        await state.update_data(list_services=list_services)

        kb = ReplyKeyboardBuilder()
        kb.row(types.KeyboardButton(
            text="📱 Отправить номер", request_contact=True))

        await callback.message.answer(
            f"Привет, {callback.from_user.first_name}! Для оформления заказа нужно подтвердить номер.",
            reply_markup=kb.as_markup(
                resize_keyboard=True, one_time_keyboard=True)
        )
        await state.set_state(AddClient.wait_phone)


@order_user_router.callback_query(MenuCallBack.filter(F.menu_name == "reduce_from_order"))
async def reduce_from_order(callback: types.CallbackQuery, callback_data: MenuCallBack, state: FSMContext, session: AsyncSession):
    user_tg_id = callback.from_user.id
    data = await state.get_data()
    service_id = callback_data.service_id
    list_services = data.get("list_services", [])

    if service_id in list_services:
        await orm_delete_from_order(session, client_id=user_tg_id, service_id=callback_data.service_id)
        list_services.remove(callback_data.service_id)
        await state.update_data(list_services=list_services)

    image, kbds = await services_menu(
        session=session,
        level=callback_data.level,
        category=callback_data.category,
        page=callback_data.page,
        state=state
    )

    try:
        await callback.message.edit_media(media=image, reply_markup=kbds)
    except Exception:
        # На случай, если пользователь нажал очень быстро и контент не изменился
        pass

    await callback.answer("Удалено из корзины ❌")
