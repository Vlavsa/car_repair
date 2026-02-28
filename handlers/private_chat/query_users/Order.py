from aiogram import F, Router, types

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto
from aiogram.types import InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


from database.Banner import orm_get_banner
from database.Client import orm_check_client
from database.Orders import orm_add_to_order, orm_delete_from_order, orm_get_orders_by_status
from filters.chat_types import ChatTypeFilter
from handlers.private_chat.query_users.Service import services_menu
from handlers.private_chat.query_users.state import AddClient
from kbds.inline.main_menu import MenuCallBack, get_client_main_btns


from database.Paginator import Paginator, pages


order_user_router = Router()
order_user_router.message.filter(ChatTypeFilter(["private"]))


async def order_menu(session, level, menu_name, state, client_id):
    # Получаем заказы со статусом 1 (в корзине)
    orders = await orm_get_orders_by_status(session, client_id, status_id=1)

    # Получаем баннер для корзины
    banner = await orm_get_banner(session, menu_name)  # menu_name тут 'order'

    if not orders:
        # Если заказов в БД нет, проверяем FSM (на случай, если юзер не зарегистрирован)
        data = await state.get_data()
        if not data.get("list_services"):
            return "🛒 <b>Ваша корзина пуста</b>", await get_client_main_btns(level=0, state=state)

    # Формируем текст чека
    order_lines = []
    total_price = 0

    # Проходим по всем заказам (обычно он один в статусе 1)
    for order in orders:
        for item in order.items:
            item_sum = item.quantity * item.price_at_runtime
            total_price += item_sum
            order_lines.append(
                f"🔹 <b>{item.service.name}</b>\n"
                f"   {item.quantity} шт. x {round(item.price_at_runtime, 2)} ₽ = {round(item_sum, 2)} ₽"
            )

    full_caption = (
        f"🛒 <b>Ваша корзина:</b>\n\n"
        f"{'\n'.join(order_lines)}\n"
        f"----------------------\n"
        f"💰 Итого к оплате: <b>{round(total_price, 2)} ₽</b>"
    )

    # Получаем кнопки для корзины (Оформить, Очистить, Назад)
    kbds = await get_order_btns(level=level, state=state, client_id=client_id)

    if banner and banner.image:
        image = InputMediaPhoto(
            media=banner.image, caption=full_caption, parse_mode="HTML")
        return image, kbds

    return full_caption, kbds


async def get_order_btns(
    *,
    level: int,
    state=None,
    sizes: tuple[int] = (1, 1, 1),
    client_id: int
):
    keyboard = InlineKeyboardBuilder()

    # Проверяем, есть ли что-то в корзине через state
    # (чтобы не показывать кнопку "Оформить", если пусто)
    data = await state.get_data() if state else {}
    cart_services = data.get("list_services", [])

    if cart_services:
        # Кнопка оформления заказа
        keyboard.add(
            InlineKeyboardButton(
                text="✅ Оформить заказ",
                callback_data=MenuCallBack(
                    level=level + 1, menu_name="checkout").pack()
            )
        )
        # Кнопка очистки
        keyboard.add(
            InlineKeyboardButton(
                text="🗑 Очистить корзину",
                callback_data=MenuCallBack(
                    level=level, menu_name="clear_cart").pack()
            )
        )

    # Кнопка возврата в каталог
    keyboard.add(
        InlineKeyboardButton(
            text="🔙 В каталог",
            callback_data=MenuCallBack(level=1, menu_name="catalog").pack()
        )
    )

    return keyboard.adjust(*sizes).as_markup()


@order_user_router.callback_query(MenuCallBack.filter(F.menu_name == "add_to_order"))
async def add_to_order(callback: types.CallbackQuery, state: FSMContext, callback_data: MenuCallBack, session: AsyncSession):

    user_tg_id = callback.from_user.id
    user = await orm_check_client(session=session, client_id=user_tg_id)

    data = await state.get_data()
    service_id = callback_data.service_id
    list_services = data.get("list_services", [])

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

        # Рекомендуется вызывать services_menu, чтобы пользователь остался на странице товара
        image, kbds = await services_menu(
            session=session,
            level=callback_data.level,
            category=callback_data.category,
            page=callback_data.page,
            state=state,
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
