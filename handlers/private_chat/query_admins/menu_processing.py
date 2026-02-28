from aiogram import types
from aiogram.types import InlineKeyboardButton, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.Paginator import Paginator
from database.Banner import orm_get_banner
from database.Category import orm_get_categories_inner_join_services, orm_get_categories, orm_get_categories_with_count_services
from database.Service import orm_get_services_by_category_id
from handlers.private_chat.query_admins.Banners import banner_menu
from handlers.private_chat.query_admins.Category import category_menu
from handlers.private_chat.query_admins.Service import services_menu
from kbds.inline.main_menu import MenuCallBackAdmin, get_admin_main_btns


async def check_image_for_menu(message: types.Message, session: AsyncSession, menu_name: str = "main", level: int = 0):
    media, replay_markup = await get_menu_content_for_admin(session, level=0, menu_name=menu_name)

    if isinstance(media, types.InputMediaPhoto):
        await message.answer_photo(
            photo=media.media,
            caption=media.caption,
            reply_markup=replay_markup,
            parse_mode="Markdown"

        )

    else:
        await message.answer(
            text=f"🖼 {media}",
            reply_markup=replay_markup)


async def main_menu(session, level, menu_name):
    kbds = get_admin_main_btns(level=level)

    return "Главное меню", kbds


async def settings_menu(session, level, menu_name):
    headline = "⚙️ Настройки деятельности и расписания:"
    keyboard = InlineKeyboardBuilder()

    # Кнопки и их соответствующие menu_name для следующего уровня (level 2)
    btns = {
        '📂 Категории': 'category',
        '🖼 Баннеры': 'banner',  # Исправил на 'banner' для соответствия дистрибьютору
        '📅 Расписание': 'time_work',
        '🔙 Назад': 'main'
    }

    for text, target_menu in btns.items():
        target_level = level - 1 if target_menu == 'main' else 2

        keyboard.add(InlineKeyboardButton(
            text=text,
            callback_data=MenuCallBackAdmin(
                level=target_level, menu_name=target_menu).pack()
        ))

    return headline, keyboard.adjust(2).as_markup()


async def order_menu(session, level, menu_name):
    print('order_menu')
    print(menu_name, level)


async def distributor_menu(session, level, menu_name, category_id, banner_id, page, state=None):
    if menu_name == "category":
        return await category_menu(session=session, level=level, menu_name=menu_name, page=page)
    elif menu_name == "banner":
        return await banner_menu(session, level, menu_name, page=page)
    elif menu_name in ["time_work", "set_time_start", "toggle_date", "set_time_end", "finalize_gen", "clear_all_free"]:
        from handlers.private_chat.query_admins.Time_work import time_work_menu
        return await time_work_menu(session, level, menu_name, state)
    else:
        return "⚠️ Меню не найдено", None


async def get_menu_content_for_admin(
    session: AsyncSession,
    level: int,
    menu_name: str,
    state: FSMContext | None = None,  # Добавили state как необязательный
    category_id: int | None = None,
    banner_id: int | None = None,
    service_id: int | None = None,
    page: int | None = 1,
):

    if level == 0:
        return await main_menu(session, level, menu_name)
    elif level == 1:
        return await settings_menu(session, level, menu_name)
    elif level == 2:
        return await distributor_menu(session, level, menu_name, category_id=category_id, banner_id=banner_id, page=page, state=state)
    elif level == 3:
        return await services_menu(session, level, menu_name, service_id, category_id, page)
    elif level == 4:
        return await order_menu(session=session, level=level)

    else:
        return "❌ Ошибка: уровень меню не определен", None


