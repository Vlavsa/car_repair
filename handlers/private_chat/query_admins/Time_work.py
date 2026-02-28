from aiogram import F, Router, types, Bot

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import or_f
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import markdown_decoration as md


from datetime import date, timedelta

from database.Paginator import Paginator, pages
from handlers.private_chat.query_admins.menu_processing import get_menu_content_for_admin
from kbds.inline.main_menu import MenuCallBackAdmin

from sqlalchemy.ext.asyncio import AsyncSession

from filters.chat_types import ChatTypeFilter, IsAdmin

from datetime import timedelta, datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler


from database.Time_work import (
    orm_book_slot,
    orm_delete_slots_on_date,
    orm_generate_slots,
    orm_get_available_dates,
    orm_get_available_slots,
    get_last_configured_date
)


time_work_router_for_admin = Router()
time_work_router_for_admin.message.filter(
    ChatTypeFilter(["private"]), IsAdmin())


class AdminTimeWork(StatesGroup):
    choosing_dates = State()
    choosing_hours = State()


async def time_work_menu(session, level, menu_name, state: FSMContext = None):
    data = await state.get_data() if state else {}
    select_dates = data.get("time_works", [])

    # --- РЕЖИМ 1: Выбор часа начала ---
    if menu_name == "set_time_start":
        text = "🕒 **Шаг 2: Выбор времени**\n\nВыберите **час начала** рабочего дня для всех выбранных дат:"
        builder = InlineKeyboardBuilder()
        for h in range(8, 21):
            builder.button(
                text=f"{h}:00",
                callback_data=MenuCallBackAdmin(
                    level=level, menu_name="set_time_end", page=h).pack()
            )
        builder.adjust(4)
        builder.row(types.InlineKeyboardButton(text="⬅️ Назад к датам",
                    callback_data=MenuCallBackAdmin(level=level, menu_name="time_work").pack()))
        return text, builder.as_markup()

    # --- РЕЖИМ 2: Выбор часа окончания ---
    elif menu_name == "set_time_end":

        start_h = data.get("start_hour", 8)
        text = f"🕒 **Шаг 3: Финал**\n\nНачало: {start_h}:00\nВыберите **час окончания** работы:"
        builder = InlineKeyboardBuilder()
        for h in range(start_h + 1, 23):
            builder.button(
                text=f"{h}:00",
                callback_data=MenuCallBackAdmin(
                    level=level, menu_name="finalize_gen", page=h).pack()
            )
        builder.adjust(4)
        return text, builder.as_markup()

    # --- РЕЖИМ 3: Основной (Выбор дат) ---
    else:
        available_dates = await orm_get_available_dates(session=session)
        active_dates_str = ", ".join(
            [md.quote(d.strftime('%d.%m')) for d in available_dates])
        # В коде формирования текста:
        dates_code = ", ".join(
            [f"`{d.strftime('%d.%m')}`" for d in available_dates])
        

        text = (
            f"📅 *Настройка рабочего времени*\n\n"
            f"✅ *Уже созданы:* {dates_code}\n\n"
            # f"✅ *Уже созданы:* {active_dates_str}\n\n"
            f"Выберите даты \(мультивыбор\):"
        )

        kbds = await get_calendar_btns(level, "time_work", select_dates)
        return text, kbds


async def get_calendar_btns(level, menu_name, select_dates):
    builder = InlineKeyboardBuilder()
    today = date.today()

    for i in range(10):
        current_date = today + timedelta(days=i)
        iso_date = current_date.isoformat()

        is_selected = iso_date in select_dates
        mark = "✅ " if is_selected else ""

        builder.button(
            text=f"{mark}{current_date.strftime('%d.%m')}",
            callback_data=MenuCallBackAdmin(
                level=level,
                menu_name="toggle_date",
                page=i  # Используем page как индекс дня
            ).pack()
        )

    builder.adjust(2)

    if select_dates:
        builder.row(types.InlineKeyboardButton(
            text=f"Настроить время ({len(select_dates)}) ➡️",
            callback_data=MenuCallBackAdmin(
                level=level, menu_name="set_time_start").pack()
        ))

    builder.row(types.InlineKeyboardButton(
        text="🗑 Удалить все записи",
        callback_data=MenuCallBackAdmin(
            level=level, menu_name="clear_all_free").pack()
    ))

    builder.row(types.InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data=MenuCallBackAdmin(level=1, menu_name="settings").pack()
    ))

    return builder.as_markup()


@time_work_router_for_admin.callback_query(MenuCallBackAdmin.filter(F.menu_name == "toggle_date"))
async def toggle_date_handler(callback: types.CallbackQuery, callback_data: MenuCallBackAdmin, state: FSMContext, session: AsyncSession):
    target_date = (
        date.today() + timedelta(days=callback_data.page)).isoformat()
    data = await state.get_data()
    selected = data.get("time_works", [])

    if target_date in selected:
        selected.remove(target_date)
    else:
        selected.append(target_date)

    await state.update_data(time_works=selected)

    # Обновляем экран через вашу общую функцию
    from handlers.private_chat.query_admins.menu_processing import get_menu_content_for_admin
    text, kb = await get_menu_content_for_admin(session, level=callback_data.level, menu_name="time_work", state=state)
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=kb
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer()  # Просто убираем иконку загрузки на кнопке
        else:
            raise e


# Хендлер выбора начала (сохраняем час и идем к выбору конца)
@time_work_router_for_admin.callback_query(MenuCallBackAdmin.filter(F.menu_name == "set_time_end"))
async def process_start_hour(callback: types.CallbackQuery, callback_data: MenuCallBackAdmin, state: FSMContext, session: AsyncSession):
    # Сохраняем выбранный час
    await state.update_data(start_hour=callback_data.page)

    from handlers.private_chat.query_admins.menu_processing import get_menu_content_for_admin
    text, kb = await get_menu_content_for_admin(session, level=callback_data.level, menu_name="set_time_end", state=state)

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=kb
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer()  # Просто убираем иконку загрузки на кнопке
        else:
            raise e

# Финальный хендлер генерации


@time_work_router_for_admin.callback_query(MenuCallBackAdmin.filter(F.menu_name == "finalize_gen"))
async def finalize_gen_handler(callback: types.CallbackQuery, callback_data: MenuCallBackAdmin, state: FSMContext, session: AsyncSession):
    end_h = callback_data.page
    data = await state.get_data()
    start_h = data.get("start_hour")
    dates = data.get("time_works", [])

    for d_str in dates:
        await orm_generate_slots(session, date.fromisoformat(d_str), start_h, end_h)

    await callback.answer("✅ Расписание создано!", show_alert=True)
    await state.clear()

    # Редирект в начало
    from handlers.private_chat.query_admins.menu_processing import get_menu_content_for_admin
    text, kb = await get_menu_content_for_admin(session, level=2, menu_name="time_work")
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=kb
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer()  # Просто убираем иконку загрузки на кнопке
        else:
            raise e


@time_work_router_for_admin.callback_query(MenuCallBackAdmin.filter(F.menu_name == "set_time_start"))
async def set_time_start_handler(callback: types.CallbackQuery, callback_data: MenuCallBackAdmin, state: FSMContext, session: AsyncSession):
    from handlers.private_chat.query_admins.menu_processing import get_menu_content_for_admin

    # Генерируем контент для режима выбора начала времени
    text, kb = await get_menu_content_for_admin(
        session,
        level=callback_data.level,
        menu_name="set_time_start",
        state=state
    )

    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except TelegramBadRequest:
        await callback.answer()


@time_work_router_for_admin.callback_query(MenuCallBackAdmin.filter(F.menu_name == "clear_all_free"))
async def clear_all_free_handler(callback: types.CallbackQuery, callback_data: MenuCallBackAdmin, state: FSMContext, session: AsyncSession):
    # 1. Удаляем свободные слоты из БД
    from database.Time_work import orm_delete_all_free_slots
    await orm_delete_all_free_slots(session)
    
    # 2. Очищаем черновик выбранных дат в FSM
    await state.update_data(time_works=[])
    
    # 3. Обновляем меню через общую функцию контента
    from handlers.private_chat.query_admins.menu_processing import get_menu_content_for_admin
    text, kb = await get_menu_content_for_admin(
        session, 
        level=callback_data.level, 
        menu_name="time_work", 
        state=state
    )
    
    await callback.answer("✅ Все свободные слоты удалены", show_alert=True)
    
    try:
        await callback.message.edit_text(text=text, reply_markup=kb, parse_mode="MarkdownV2")
    except TelegramBadRequest:
        await callback.answer()