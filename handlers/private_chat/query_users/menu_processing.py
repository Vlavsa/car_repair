from aiogram import types
from aiogram.types import InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.context import FSMContext


from database.Paginator import Paginator, pages
from database.Banner import orm_get_banner
from database.Category import orm_get_categories_inner_join_services
from database.Service import orm_get_services_by_category_id
from handlers.private_chat.query_users.Service import get_service_btns, services_menu
from kbds.inline.main_menu import MenuCallBack, get_client_main_btns
from kbds.inline.inline import get_user_catalog_btns



async def check_image_for_menu(message: types.Message, session: AsyncSession, menu_name: str = "main"):
    media, replay_markup = await get_menu_content(session, level=0, menu_name=menu_name)

    if isinstance(media, types.InputMediaPhoto):
        await message.answer_photo(
            photo=media.media,
            caption=media.caption,
            reply_markup=replay_markup
        )

    else:
        await message.answer(
            text=f"🖼 (Изображение отсутствует для {media.name})\n\n{media.description}",
            reply_markup=replay_markup)


async def main_menu(session, level, menu_name):
    banner = await orm_get_banner(session, menu_name)
    kbds = get_client_main_btns(level=level)

    if not banner.image:
        return banner, kbds

    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    return image, kbds


async def catalog_menu(session, level, menu_name):
    banner = await orm_get_banner(session=session, page=menu_name)
    categories = await orm_get_categories_inner_join_services(session=session)

    kbds = get_user_catalog_btns(level=level, categories=categories)

    if not banner.image:
        return banner, kbds

    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    return image, kbds




async def order_menu(session, level, menu_name):
    ...


async def get_menu_content(
        session: AsyncSession,
        level: int,
        menu_name: str,
        category: int | None = None,
        page: int | None = None,
        state: FSMContext | None = None,
):

    if level == 0:
        return await main_menu(session, level, menu_name)
    elif level == 1:
        return await catalog_menu(session, level, menu_name)
    elif level == 2:
        return await services_menu(session, level, category, page, state)
    