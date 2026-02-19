from aiogram import F, Router, types

from aiogram.types import InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, StateFilter, or_f
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder


from database.Paginator import Paginator, pages
from kbds.inline.categories_admin import CategoryClick, get_paginated_categories_kb
from kbds.inline.main_menu import MenuCallBackAdmin
from kbds.reply import ADMIN_KB

from sqlalchemy.ext.asyncio import AsyncSession

from filters.chat_types import ChatTypeFilter, IsAdmin

from database.Category import (
    orm_add_category,
    orm_create_categories,
    orm_delete_category,
    orm_get_categories,
    orm_get_categories_inner_join_services,
    orm_get_categories_with_count_services,
    orm_get_category,
    orm_update_category,
)


from kbds.inline.inline import get_callback_btns, button_categories_admin, button_settings_admin, buttons_start_admin


category_router_for_admin = Router()
category_router_for_admin.message.filter(
    ChatTypeFilter(["private"]), IsAdmin())


class ClickCategory(CallbackData, prefix="category_"):
    pref: str  # "delete", "update", "confirm_delete"
    category_id: int | None = None
    category_name: str | None = None
    page: int | None = 1  # Текущая страница пагинации


class AddCategory(StatesGroup):
    # Шаги состояний
    name = State()

    texts = {
        "AddCategory:name": "Введите название заново:",
    }


async def category_menu(session, level, menu_name, page):
    categories = await orm_get_categories_with_count_services(session=session)

    if not categories:
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(
            text='➕ Создать категорию', callback_data='add_category'))
        kb.add(InlineKeyboardButton(text='🔙 Назад', callback_data=MenuCallBackAdmin(
            level=level-1, menu_name='settings').pack()))
        return "📂 Список категорий пуст...", kb.adjust(1).as_markup()

    # Пагинация
    paginator = Paginator(categories, page=page)

    if not paginator.get_page():
        page = paginator.pages
        paginator = Paginator(categories, page=page)

    page_data = paginator.get_page()
    category, count = page_data[0]

    headline = (
        f"🗄 **Категория: {category.name}**\n"
        f"────────────────────\n"
        f"📊 Всего услуг в базе: {count}\n"
    )

    # Кнопки управления и пагинации
    pagination_btns = pages(paginator)
    kb_builder = get_categories_btns(
        level=level,
        page=page,
        category=category,  # Передаем сам объект категории
        pagination_btns=pagination_btns
    )

    # Добавляем общие кнопки управления меню
    kb_builder.row(
        InlineKeyboardButton(text='➕ Создать новую',
                             callback_data='add_category'),
        InlineKeyboardButton(text='🔙 Назад', callback_data=MenuCallBackAdmin(
            level=level-1, menu_name='settings').pack())
    )
    return headline, kb_builder.as_markup()


def get_categories_btns(
    *,
    page: int,
    level: int,
    category: object,
    pagination_btns: dict,
    sizes: tuple[int] = (2,),
):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(
        InlineKeyboardButton(text="🗑 Удалить", callback_data=ClickCategory(
            category_id=category.id, category_name=category.name, pref="delete", page=page).pack()),
        InlineKeyboardButton(text="✏️ Изменить", callback_data=ClickCategory(
            category_id=category.id, category_name=category.name, pref="update", page=page).pack()),
        InlineKeyboardButton(text="📂 Услуги", callback_data=MenuCallBackAdmin(
            level=level+1, menu_name="services", category_id=category.id).pack())
    )

    keyboard.adjust(*sizes)

    # Ряд пагинации
    nav_row = []
    for text, action in pagination_btns.items():
        if action == "next":
            nav_row.append(InlineKeyboardButton(text=text, callback_data=MenuCallBackAdmin(
                level=level, menu_name="category", page=page + 1).pack()))
        elif action == "prev":
            nav_row.append(InlineKeyboardButton(text=text, callback_data=MenuCallBackAdmin(
                level=level, menu_name="category", page=page - 1).pack()))

    if nav_row:
        keyboard.row(*nav_row)

    return keyboard


# Хендлер добавления категории
@category_router_for_admin.callback_query(F.data == "add_category")
async def start_add_category(callback: types.CallbackQuery, state: FSMContext):
    # Запоминаем ID сообщения, которое будем редактировать на протяжении всего процесса
    await state.update_data(msg_to_edit=callback.message.message_id)
    await state.set_state(AddCategory.name)

    await callback.message.edit_text(
        "📝 **Режим добавления**\n_____________________\nВведите название для новой категории:",
        reply_markup=InlineKeyboardBuilder().button(
            text="❌ Отмена", callback_data="cancel_add_category").as_markup()
    )
    await callback.answer()


@category_router_for_admin.callback_query(ClickCategory.filter(F.pref == "delete"))
async def ask_delete(callback: types.CallbackQuery, callback_data: ClickCategory):
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(text="✅ Да, удалить",
                             callback_data=ClickCategory(pref="confirm_delete", category_id=callback_data.category_id, page=callback_data.page).pack()),
        InlineKeyboardButton(text="❌ Отмена",
                             callback_data=MenuCallBackAdmin(level=2, menu_name="category", page=callback_data.page).pack())
    )
    await callback.message.edit_text(f"⚠️ Удалить категорию: {callback_data.category_name}?", reply_markup=kb.as_markup())


@category_router_for_admin.callback_query(ClickCategory.filter(F.pref == "confirm_delete"))
async def delete_cat(callback: types.CallbackQuery, callback_data: ClickCategory, session: AsyncSession):
    await orm_delete_category(session, callback_data.category_id)
    await session.commit()

    await callback.answer("Удалено")

    from .menu_processing import get_menu_content_for_admin
    content, reply_markup = await get_menu_content_for_admin(session, level=2, menu_name="category", page=callback_data.page)
    await callback.message.edit_text(text=content, reply_markup=reply_markup)


@category_router_for_admin.callback_query(ClickCategory.filter(F.pref == "update"))
async def edit_cat_start(callback: types.CallbackQuery, callback_data: ClickCategory, state: FSMContext):
    await state.set_state(AddCategory.name)
    await state.update_data(
        edit_category_id=callback_data.category_id,
        return_page=callback_data.page,
        msg_to_edit=callback.message.message_id
    )

    await callback.message.edit_text(
        f"📝 **Режим редактирования**\n\nВведите новое название для {callback_data.category_name}:",
        reply_markup=InlineKeyboardBuilder().button(
            text="❌ Отмена", callback_data="cancel_add").as_markup()
    )
    await callback.answer()


@category_router_for_admin.message(AddCategory.name, F.text)
async def save_category_logic(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    msg_id = data.get("msg_to_edit")
    cat_id = data.get("edit_category_id")
    page = data.get("return_page", 1)

    # 1. Проверка длины текста
    if not (3 <= len(message.text) <= 30):
        await message.delete()  # Удаляем некорректный ввод юзера

        # Редактируем сообщение бота, добавляя предупреждение
        error_text = (
            f"❌ **Ошибка: слишком {'короткое' if len(message.text) < 3 else 'длинное'} название!**\n"
            f"Должно быть от 3 до 30 символов (сейчас: {len(message.text)})\n\n"
            "Введите название заново:"
        )

        if msg_id:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=msg_id,
                text=error_text,
                reply_markup=InlineKeyboardBuilder().button(
                    text="❌ Отмена", callback_data="cancel_add_category").as_markup(),
                parse_mode="Markdown"
            )
        return  # Выходим из функции, состояние AddCategory.name сохраняется

    # 1. Сначала логика БД и подготовка данных
    if cat_id:
        await orm_update_category(session, cat_id, {"name": message.text})
        success_text = f"✅ Название изменено на «{message.text}»"
    else:
        await orm_add_category(session, {"name": message.text})
        success_text = f"✅ Категория «{message.text}» создана"
        # Пересчитываем страницу для новой категории
        categories_all = await orm_get_categories_with_count_services(session)
        page = len(categories_all)

    await session.commit()
    await state.clear()

    # 2. Получаем контент для возврата в меню
    headline, kb = await category_menu(session, level=2, menu_name="category", page=page)
    full_text = f"{success_text}\n\n{headline}"

    # 3. Чистим сообщение пользователя
    await message.delete()

    # 4. Бесшовное обновление или отправка нового сообщения
    if msg_id:
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=msg_id,
                text=full_text,
                reply_markup=kb,
                parse_mode="Markdown"
            )
            return  # Выходим, если успешно отредактировали
        except Exception:
            pass  # Если сообщение бота удалено или устарело, переходим к .answer()

    # Если msg_id нет или edit_text не сработал
    await message.answer(full_text, reply_markup=kb, parse_mode="Markdown")


@category_router_for_admin.callback_query(F.data == "cancel_add_category")
async def cancel_add_category(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    page = data.get("return_page", 1)
    await state.clear()

    # Просто возвращаем меню категорий в то же сообщение
    headline, kb = await category_menu(session, level=2, menu_name="category", page=page)
    await callback.message.edit_text(text=headline, reply_markup=kb, parse_mode="Markdown")
    await callback.answer("Действие отменено")
