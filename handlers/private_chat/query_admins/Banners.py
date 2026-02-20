from aiogram import F, Router, types


from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, StateFilter, or_f
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder


from callback.banner_admins_btns import BannerClick
from database.Paginator import Paginator, pages
from kbds.inline.inline import get_callback_btns
from kbds.inline.main_menu import MenuCallBackAdmin
from kbds.reply import get_keyboard, ADMIN_KB

from sqlalchemy.ext.asyncio import AsyncSession

from filters.chat_types import ChatTypeFilter, IsAdmin

from database.Banner import (
    orm_get_banners,
    orm_add_banner_description,
    orm_change_banner_image,
    orm_get_banner,
    orm_get_info_pages,
    orm_update_banner_image
)

from kbds.inline.inline import button_banner_admin


banner_router_for_admin = Router()
banner_router_for_admin.message.filter(ChatTypeFilter(["private"]), IsAdmin())


################# Микро FSM для загрузки/изменения баннеров ############################

class AddBanner(StatesGroup):
    image = State()
    description = State()
    banner_for_change = {}

class ClickBanner(CallbackData, prefix="banner_"):
    pref: str # update
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
        f"_____________________\n"
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

    return media, kb_builder

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

    kb_builder.button(text="✏️ Изменить", callback_data=ClickBanner(pref="update", banner_id=banner.id, page=page))
    kb_builder.adjust(*sizes)

    
    nav_row = []

    for text, action in pagination_btns.items():
        target_page = page + 1 if action == "next" else page - 1

        nav_row.append(types.InlineKeyboardButton(
            text=text,
            callback_data=MenuCallBackAdmin(
                level = level,
                menu_name= menu_name,
                page=target_page
            ).pack()

        ))

    if nav_row:
        kb_builder.row(*nav_row)

    return kb_builder

@banner_router_for_admin.callback_query(F.data == 'banners')
async def banners_menu(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    await callback.message.edit_text(
        text="Настройка баннеров:",
        reply_markup=button_banner_admin)


@banner_router_for_admin.callback_query(F.data == 'banners_list')
async def cmd_show_banners(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    # 1. Запрос к БД
    banners = await orm_get_banners(session)

    if not banners:
        await callback.answer()
        return await callback.message.answer('Баннеры еще не добавлены.')

    await callback.message.delete()
    await callback.answer()
    for row in banners:
        builder = InlineKeyboardBuilder()
        # Данная затея не рассматривается
        # builder.button(
        #     text="🗑 Удалить",
        #     callback_data=BannerClick(
        #         action="delete", banner_id=row.id, banner_name=row.name)
        # )
        builder.button(
            text="✏️ Редактирать",
            callback_data=BannerClick(
                action="edit", banner_id=row.id, banner_name=row.name)
        )
        builder.adjust(2,)  # Кнопки одна под другой
        if row.image:
            await callback.message.answer_photo(
                photo=row.image,
                caption=row.description,
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )
        else:
            # Если картинки нет, отправляем просто текст, чтобы бот не падал
            await callback.message.answer(
                text=f"🖼 (Изображение отсутствует для {row.name})\nВаш текст баннера...\n**{row.description}**",
                reply_markup=builder.as_markup()
            )
    await callback.message.answer(text='Настройка Баннеров', reply_markup=button_banner_admin)


@banner_router_for_admin.callback_query(BannerClick.filter(F.action == 'edit'))
async def edit_banner(
    callback: types.CallbackQuery,
    callback_data: BannerClick,
    state: FSMContext,  # Добавляем FSM
    session: AsyncSession
):
    await callback.message.delete()
    await callback.answer()
    await state.update_data(edit_banner_id=callback_data.banner_id)

    # await state.set_state(AddBanner.image)
    await state.set_state(AddBanner.image)
    await callback.message.answer(
        f"Загрузите фото для баннера (name: {callback_data.banner_name}):"
    )

    await callback.answer()


@banner_router_for_admin.message(AddBanner.image, F.photo)
async def add_banner(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    banner_id = data.get('edit_banner_id')
    try:
        image_id = message.photo[-1].file_id

        # Обновляем запись по уникальному banner_id (Primary Key)
        # Это гарантирует изменение ровно одной нужной строки
        await orm_update_banner_image(
            session=session,
            banner_id=banner_id,
            image=image_id
        )

        await message.answer("Баннер успешно обновлен.", reply_markup=button_banner_admin)
        await state.clear()
    except Exception as e:
        await message.answer(f"Ошибка при сохранении: {e}")
# ловим некоррекный ввод


@banner_router_for_admin.message(AddBanner.image)
async def add_banner2(message: types.Message, state: FSMContext):
    await message.answer("Отправьте фото баннера или отмена")
