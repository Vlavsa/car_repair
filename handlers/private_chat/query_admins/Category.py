from aiogram import F, Router, types


from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder


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


class AddCategory(StatesGroup):
    # Шаги состояний
    name = State()

    texts = {
        "AddCategory:name": "Введите название заново:",
    }


@category_router_for_admin.callback_query(F.data == 'categories')
async def categories_menu(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    await callback.message.edit_text(
        text="Настройка категорий:",
        reply_markup=button_categories_admin)


@category_router_for_admin.callback_query(MenuCallBackAdmin.filter(F.data == 'categories_list'))
async def cmd_show_categories(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    # 1. Запрос к БД
    categories = await orm_get_categories_with_count_services(session)

    if not categories:
        await callback.answer()
        return await callback.message.answer("Категорий пока нет.")

    await callback.message.delete()
    await callback.answer()
    # 2. Перебор данных и отправка сообщений (карточек)
    for row in categories:
        category = row[0]  # Объект Category
        count = row[1]     # Результат count
        # Создаем кнопки именно для этой карточки
        builder = InlineKeyboardBuilder()
        builder.button(
            text="📖 Список",
            callback_data=CategoryClick(
                action="category_", category_id=category.id)
        )
        builder.button(
            text="🗑 Удалить",
            callback_data=CategoryClick(
                action="delete", category_id=category.id)
        )
        builder.button(
            text="✏️ Редактирать",
            callback_data=CategoryClick(
                action="edit", category_id=category.id)
        )
        builder.adjust(1, 2)  # Кнопки одна под другой

        # Отправляем сообщение-карточку
        await callback.message.answer(
            text=(
                f"🗄 **Категория: {category.name}**\n"
                f"────────────────────\n"
                f"\n"
                f"📊 Всего услуг в базе: {count}\n"
            ),
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
    await callback.message.answer(
        text="Настройки категорий:",
        reply_markup=button_categories_admin)


@category_router_for_admin.callback_query(CategoryClick.filter(F.action == "delete"))
async def ask_delete_confirmation(callback: types.CallbackQuery, callback_data: CategoryClick):
    builder = InlineKeyboardBuilder()

    # Кнопка подтверждения и кнопка отмены
    builder.button(
        text="✅ Да, удалить",
        callback_data=CategoryClick(
            action="confirm_delete", category_id=callback_data.category_id)
    )
    builder.button(
        text="❌ Отмена",
        callback_data=CategoryClick(
            action="cancel", category_id=callback_data.category_id)
    )

    await callback.message.edit_text(
        text=f"⚠️ **Вы уверены, что хотите удалить эту категорию?**\nВсе связанные услуги также могут быть затронуты.",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@category_router_for_admin.callback_query(CategoryClick.filter(F.action == 'edit'))
async def edit_category(
    callback: types.CallbackQuery,
    callback_data: CategoryClick,
    state: FSMContext,  # Добавляем FSM
    session: AsyncSession
):
    # 2. Сохраняем ID категории, которую редактируем
    await state.update_data(edit_category_id=callback_data.category_id)

    # 3. Устанавливаем состояние ожидания текста
    await state.set_state(AddCategory.name)

    await callback.message.answer(
        f"Введите новое название для категории (ID: {callback_data.category_id}):"
    )

    await callback.answer()


@category_router_for_admin.callback_query(CategoryClick.filter(F.action == "confirm_delete"))
async def delete_category_confirmed(callback: types.CallbackQuery, callback_data: CategoryClick, session: AsyncSession):
    # Удаление из БД

    await orm_delete_category(session=session, category_id=callback_data.category_id)
    await session.commit()

    await callback.message.edit_text("🗑 Категория успешно удалена.")
    await callback.answer("Удалено")


@category_router_for_admin.callback_query(CategoryClick.filter(F.action == "cancel"))
async def cancel_delete(callback: types.CallbackQuery):

    await callback.message.delete()
    await callback.answer("Действие отменено")


@category_router_for_admin.callback_query(F.data == "add_category")
async def add_category(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer('Введите название категории: ', reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddCategory.name)


@category_router_for_admin.message(AddCategory.name, F.text)
async def save_category_logic(message: types.Message, state: FSMContext, session: AsyncSession):
    if len(message.text) <= 3:
        await message.answer("Название слишком короткое! Введите заново.")
        return

    data = await state.get_data()
    category_id = data.get("edit_category_id")

    payload = {"name": message.text}

    try:
        if category_id:
            await orm_update_category(session, category_id, payload)
            await message.answer(f"✅ Название изменено на: **{message.text}**")
        else:
            # ДОБАВЛЕНИЕ
            await orm_add_category(session, payload)
            await message.answer("✅ Категория добавлена", reply_markup=button_categories_admin)

        # Финальный коммит, если он не сделан внутри функций
        await state.clear()

    except Exception as e:
        # Если снова будет ошибка, мы увидим, на чем именно споткнулся код
        await message.answer(f"Ошибка при сохранении: {e}")
