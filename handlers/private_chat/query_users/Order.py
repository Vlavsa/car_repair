from aiogram import Router, types, F
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


    banner = await orm_get_banner(session, page="order")
    orders = await orm_get_orders_by_status(
        session=session, client_id=client_id, status_id=status_id)
    

    if not orders:
        caption = "<b>Корзина пуста...</b>"
    else:
        final_total = 0 
        caption = f"📦 <b>Ваш заказ</b>\n"
        for order in orders:
            print(order.items)
            order_sum = 0 
            
            for item in order.items:
                print(item.__dict__)

                service_name = item.service.name
                service_price = item.service.price
                
                quantity = getattr(item, 'quantity', 1) 
                
                item_total = service_price * quantity
                order_sum += item_total
                
                caption += f" — {service_name}: {quantity} шт. x {service_price} руб. = {item_total} руб.\n"
            
            caption += f"👉 <i>Сумма по заказу: {order_sum} руб.</i>\n"
            final_total += order_sum
        
        caption += f"\n💰 <b>ИТОГО К ОПЛАТЕ: {final_total} руб.</b>"


    if not banner or not banner.image:
        image = caption

    else:
        image = InputMediaPhoto(
            media=banner.image,
            caption=caption,
            parse_mode="HTML"
        )

    kb_builder = InlineKeyboardBuilder()
   
    button_text_prev = "main" if not category else "category"

    kb_builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data=MenuCallBack(
        level=0, menu_name=button_text_prev, category=category, page=page).pack()))

    if not orders:
        return image, kb_builder.as_markup()



    return image, kb_builder.as_markup()



@order_for_user_router.callback_query(MenuCallBack.filter(F.menu_name == "add_to_order"))
async def handler_add_order(session: AsyncSession, callback: types.CallbackQuery, callback_data: MenuCallBack, state: FSMContext):

    if state is not None:
        data = await state.get_data()

        cart_services = [int(i) for i in data.get("list_services", [])]
    else:
        cart_services = []
    print(callback_data.__dict__)

    # callback_data = level=level, menu_name=menu_action, category=category, service_id=service_id, page=page
