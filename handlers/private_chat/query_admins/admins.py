from aiogram import F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext


from sqlalchemy.ext.asyncio import AsyncSession

from handlers.private_chat.query_admins.Service import service_router_for_admin
from handlers.private_chat.query_admins.Banners import banner_router_for_admin
from handlers.private_chat.query_admins.Category import category_router_for_admin

from filters.chat_types import ChatTypeFilter, IsAdmin

from handlers.private_chat.query_admins.menu_processing import get_menu_content_for_admin, check_image_for_menu
from kbds.inline.inline import get_callback_btns, button_categories_admin, button_settings_admin, buttons_start_admin
from kbds.inline.main_menu import MenuCallBackAdmin
from kbds.reply import get_keyboard
from middlewares.cleanOnStart import CleanOnStartMiddleware

admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())


# admin_router.callback_query.middleware(CleanOnStartMiddleware()) # ??????????????????????????


# @admin_router.message(Command("admin"))
# async def get_main_menu_admins(message: types.Message):
#     return await message.answer(text="Главное меню админа:", reply_markup=buttons_start_admin)

@admin_router.message(Command("admin"))
async def start_admin_menu(message: types.Message, session: AsyncSession, menu_name: str = "main"):
    await check_image_for_menu(message=message, session=session, menu_name=menu_name, level=0)


@admin_router.callback_query(MenuCallBackAdmin.filter())
async def user_menu(callback: types.CallbackQuery, callback_data: MenuCallBackAdmin, session: AsyncSession):
    media, replay_markup = await get_menu_content_for_admin(
        session,
        level=callback_data.level,
        menu_name=callback_data.menu_name,
        category_id=callback_data.category_id,
        page=callback_data.page,
    )

    if callback.message.text and isinstance(media, types.InputMediaPhoto):
        await callback.message.delete()  # Удаляем старый текст
        await callback.message.answer_photo(  # Отправляем новое фото
            photo=media.media,
            caption=media.caption,
            reply_markup=replay_markup,
            parse_mode="Markdown"
        )

    elif callback.message.photo and isinstance(media, types.InputMediaPhoto):
        await callback.message.edit_media(
            media=media,  # Передаем объект целиком
            reply_markup=replay_markup,
            parse_mode="Markdown"
        )

    elif callback.message.photo and not isinstance(media, types.InputMediaPhoto):
        await callback.message.delete()  # Удаляем фото
        await callback.message.answer(   # Отправляем чистый текст
            text=f"🖼 {media}",
            reply_markup=replay_markup,
            parse_mode="Markdown"
        )

    else:
        await callback.message.edit_text(
            text=f"🖼 {media}",
            reply_markup=replay_markup,
            parse_mode="Markdown"
        )

    await callback.answer()


admin_router.include_routers(
    banner_router_for_admin,
    category_router_for_admin,
    service_router_for_admin,
)
