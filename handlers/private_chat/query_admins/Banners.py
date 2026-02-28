from aiogram import F, Router, types


from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import or_f
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder


from database.Paginator import Paginator, pages
from handlers.private_chat.query_admins.Service import edit_smart

from kbds.inline.main_menu import MenuCallBackAdmin

from sqlalchemy.ext.asyncio import AsyncSession

from filters.chat_types import ChatTypeFilter, IsAdmin

from database.Banner import (
    orm_get_banners,
    orm_add_banner_description,
    orm_change_banner_image,
    orm_get_banner,
    orm_get_banner_by_id,
    orm_get_info_pages,
    orm_update_banner_by_id,
    orm_update_banner_image
)


banner_router_for_admin = Router()
banner_router_for_admin.message.filter(ChatTypeFilter(["private"]), IsAdmin())


################# Микро FSM для загрузки/изменения баннеров ############################

class AddBanner(StatesGroup):
    image = State()
    description = State()
    banner_for_change = {}


class ClickBanner(CallbackData, prefix="banner_"):
    pref: str  # update
    banner_id: int
    page: int | None = 1


async def banner_menu(session, level, menu_name, page):
    banners = await orm_get_banners(session=session)

    kb_builder = InlineKeyboardBuilder()

    kb_builder.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data=MenuCallBackAdmin(
        level=level-1, menu_name="settings").pack()))

    if not banners:
        headline = "Баннеры не работают, звони Владу!!!"
        return headline, kb_builder.adjust(1).as_markup()

    paginator = Paginator(banners, page=page)
    if not paginator.get_page():
        page = paginator.pages
        paginator = Paginator(banners, page=page)

    current_banner = paginator.get_page()[0]
    pagination_btns = pages(paginator=paginator)
    image_warning = "" if current_banner.image else "⚠️ Добавьте фото для этого баннера!\n\n"
    caption = (
        f"{image_warning}"
        f"🖼 **Баннер: {current_banner.name}**\n"
        f"────────────────────\n"
        f"📝 {current_banner.description or 'Описание отсутствует'}"
    )
    if current_banner.image:
        media = types.InputMediaPhoto(
            media=current_banner.image,
            caption=caption,
            parse_mode="Markdown"
        )
    else:
        media = caption

    kb_b = await get_banners_btns(level=level, menu_name=menu_name, banner=current_banner, pagination_btns=pagination_btns, page=page)
    kb_builder.attach(kb_b)

    return media, kb_builder.as_markup()


async def get_banners_btns(
        *,
        level: int,
        page: int,
        menu_name: str,
        banner: object,
        pagination_btns: dict,
        sizes: tuple[int] = (2,),
):
    kb_builder = InlineKeyboardBuilder()

    kb_builder.button(text="✏️ Изменить", callback_data=ClickBanner(
        pref="update", banner_id=banner.id, page=page))
    kb_builder.adjust(*sizes)

    nav_row = []

    for text, action in pagination_btns.items():
        target_page = page + 1 if action == "next" else page - 1

        nav_row.append(types.InlineKeyboardButton(
            text=text,
            callback_data=MenuCallBackAdmin(
                level=level,
                menu_name=menu_name,
                page=target_page
            ).pack()

        ))

    if nav_row:
        kb_builder.row(*nav_row)

    return kb_builder


@banner_router_for_admin.callback_query(ClickBanner.filter(F.pref == "update"))
async def start_update_banners(callback: types.CallbackQuery, callback_data: ClickBanner, session: AsyncSession, state: FSMContext):
    banner_id = callback_data.banner_id
    banner = await orm_get_banner_by_id(session=session, banner_id=banner_id)

    await state.update_data(
        msg_to_edit=callback.message.message_id,
        return_page=callback_data.page,
        old_banner_id=banner.id,
        old_description=banner.description,
        old_image=banner.image
    )  # name, description, image

    await state.set_state(AddBanner.description)
    text = (
        f"✏️ **Редактирование баннера**\n"
        f"Текущее описание: **{banner.description or 'пусто'}**\n\n"
        f"Введите новое описание или '.' чтобы оставить прежнее:"
    )

    kb = InlineKeyboardBuilder().button(
        text="❌ Отмена", callback_data="cancel_add_banner"
    ).as_markup()

    try:
        await callback.message.edit_caption(caption=text, reply_markup=kb, parse_mode="Markdown")
    except TelegramBadRequest:
        try:
            await callback.message.edit_text(text=text, reply_markup=kb, parse_mode="Markdown")
        except TelegramBadRequest:
            await callback.message.delete()
            new_msg = await callback.message.answer(text=text, reply_markup=kb, parse_mode="Markdown")
            await state.update_data(msg_to_edit=new_msg.message_id)

    await callback.answer()


@banner_router_for_admin.callback_query(F.data == "cancel_add_banner")
async def cancel_add_banner(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    page = data.get("return_page", 1)

    await state.clear()

    from .menu_processing import get_menu_content_for_admin
    content, reply_markup = await get_menu_content_for_admin(
        session=session, level=2, menu_name="banner", page=page
    )

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    if isinstance(content, types.InputMediaPhoto):
        await callback.message.answer_photo(
            photo=content.media,
            caption=content.caption,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await callback.message.answer(
            text=content,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    await callback.answer()


@banner_router_for_admin.message(AddBanner.description, or_f(F.text == ".", F.text))
async def add_banner_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    banner_id = data.get("old_banner_id")
    msg_id = data.get("msg_to_edit")

    await message.delete()

    kb = InlineKeyboardBuilder().button(
        text="❌ Отмена", callback_data="cancel_add_banner"
    ).as_markup()

    if message.text == "." and banner_id:
        new_description = data.get("old_description")
    else:
        if len(message.text) >= 300:
            error_text = (
                f"❌ **Ошибка: слишком длинное описание!**\n"
                f"Должно быть до 300 символов (сейчас: {len(message.text)})\n\n"
                f"Введите описание заново{' или \".\"' if banner_id else ''}:"
            )
            return edit_smart(message=message, msg_id=msg_id, text=error_text, keyboard=kb)
        new_description = message.text

    await state.update_data(description=new_description)
    await state.set_state(AddBanner.image)
    next_text = (
        f"✅ Описание принято.\n\n"
        f"📸 Теперь загрузите **фото** баннера или {'. если оставить прежнюю' if banner_id else 'отправьте изображение'}:"
    )
    await edit_smart(message, msg_id, next_text, keyboard=kb)


@banner_router_for_admin.message(AddBanner.image, F.photo)
async def add_banner_image(message: types.Message, state: FSMContext, session: AsyncSession):

    photo_id = message.photo[-1].file_id
    data = await state.get_data()

    await state.update_data(image=photo_id)

    await message.delete()
    await proceed_to_save(message, state, session)


@banner_router_for_admin.message(AddBanner.image, F.text == ".")
async def skip_banner_image(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()

    if not data.get("old_banner_id"):
        kb = InlineKeyboardBuilder().button(
            text="❌ Отмена", callback_data="cancel_add_banner"
        ).as_markup()
        return await edit_smart(message, data.get("msg_to_edit"), "❌ Для нового баннера фото обязательно! Отправьте изображение:", keyboard=kb)

    await state.update_data(image=data.get("old_image"))
    await message.delete()
    await proceed_to_save(message, state, session)


async def proceed_to_save(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    page = data.get("return_page", 1)
    msg_id = data.get("msg_to_edit")
    banner_id = data.get("old_banner_id")
    data_sent = {
        "description": data.get("description"),
        "image": data.get("image"),
    }

    kb = InlineKeyboardBuilder().button(
        text="🔙 К списку баннеров",
        callback_data=MenuCallBackAdmin(
            level=2, menu_name="banner", page=page)
    ).as_markup()
    try:
        if banner_id:
            await orm_update_banner_by_id(session, banner_id, data_sent)
            text = "✅ Баннер успешно обновлен!"

        else:
            text = "❌ Баннеры нельзя добавлять через это меню!"

        await session.commit()
        await state.clear()

        await edit_smart(message, msg_id, text, keyboard=kb)

    except Exception as e:
        print(e)
        await session.rollback()
        await edit_smart(message, msg_id, f"❌ Ошибка при сохранении.", kb)
