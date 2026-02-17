from aiogram import types
from aiogram.types import InlineKeyboardButton, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from database.Paginator import Paginator
from database.Banner import orm_get_banner
from database.Category import orm_get_categories_inner_join_services, orm_get_categories, orm_get_categories_with_count_services
from database.Service import orm_get_services_by_category_id
from kbds.inline.main_menu import MenuCallBackAdmin, get_admin_main_btns, get_client_main_btns
from kbds.inline.inline import get_callback_btns, get_products_btns, get_user_catalog_btns


async def check_image_for_menu(message: types.Message, session: AsyncSession, menu_name: str = "main", level: int = 0):
    media, replay_markup = await get_menu_content_for_admin(session, level=0, menu_name=menu_name)

    if isinstance(media, types.InputMediaPhoto):
        await message.answer_photo(
            photo=media.media,
            caption=media.caption,
            reply_markup=replay_markup
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

    print(headline)
    return headline, keyboard.adjust(2).as_markup()


async def category_menu(session, level, menu_name):
    categories = await orm_get_categories_with_count_services(session=session)
    keyboard = InlineKeyboardBuilder()
    headline = " Настройка категорий: "

    btns = {
        "Создать": "add_category",
        '🔙 Назад': 'setting'
    }


    for text, target_menu in btns.items():
        if menu_name == "setting":
            keyboard.add(InlineKeyboardButton(text=text, callback_data=MenuCallBackAdmin(
                level=level-1, menu_name=target_menu).pack()))
        # keyboard.add(InlineKeyboardButton(text=text, callback_data=MenuCallBackAdmin(
        #     level=level+1, menu_name=target_menu).pack()))
    return headline, keyboard.adjust(2).as_markup()


async def banner_menu(session, level, menu_name):
    print('banner_menu')
    print(menu_name, level)


async def time_work_menu(session, level, menu_name):
    print('time_work_menu')
    print(menu_name, level)


async def order_menu(session, level, menu_name):
    print('order_menu')
    print(menu_name, level)


async def service_menu(session, level, menu_name):
    print('service_menu')
    print(menu_name, level)


async def distributor_menu(session, level, menu_name):
    if menu_name == "category":
        return await category_menu(session=session, level=level, menu_name=menu_name)
    elif menu_name == "banner":
        return await banner_menu(session, level, menu_name)
    elif menu_name == "time_work":
        return await time_work_menu(session, level, menu_name)


async def get_menu_content_for_admin(
        session: AsyncSession,
        level: int,
        menu_name: str,
        category: int | None = None,
        page: int | None = None,
):

    if level == 0:
        print('000000000000000000000000000000000000000000')
        return await main_menu(session, level, menu_name)
    elif level == 1:
        print('111111111111111111111111111111111111111111')
        return await settings_menu(session, level, menu_name)
    elif level == 2:
        return await distributor_menu(session, level, menu_name)
    elif level == 4:
        return await order_menu(session=session, level=level)
