from decimal import Decimal, InvalidOperation
from aiogram import F, Router, types

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton, InputMediaPhoto
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder


from database.Paginator import Paginator, pages
from kbds.inline.main_menu import MenuCallBackAdmin
from kbds.reply import ADMIN_KB

from sqlalchemy.ext.asyncio import AsyncSession

from filters.chat_types import ChatTypeFilter, IsAdmin

from database.Service import (
    orm_add_service,
    orm_delete_service_by_id,
    orm_get_service_by_id,
    orm_get_services_by_category_id,
    orm_update_service_by_id,

)
from database.Category import (
    orm_get_categories,
)


service_router_for_admin = Router()
service_router_for_admin.message.filter(ChatTypeFilter(["private"]), IsAdmin())


######################### FSM для дабавления/изменения товаров админом ###################
class ClickService(CallbackData, prefix="service_"):
    pref: str  # delete, update, confirm_delete
    category_id: int | None = None
    service_id: int | None = None
    service_name: str | None = None
    page: int | None = 1


class AddService(StatesGroup):
    name = State()
    description = State()
    category = State()
    price = State()
    image = State()


async def services_menu(
    session,
    level,
    menu_name,
    service_id,
    category_id,
    page
):
    services = await orm_get_services_by_category_id(session=session, category_id=category_id)

    if not services:
        kb = InlineKeyboardBuilder()
        kb.row(types.InlineKeyboardButton(text='🔙 Назад',
               callback_data=MenuCallBackAdmin(level=level-1, menu_name='category').pack()))
        kb.row(types.InlineKeyboardButton(text='➕ Добавить услугу',
               callback_data=ClickService(pref="add_service", category_id=category_id).pack()))
        
        return "📂 Услуг в этой категории пока нет", kb.as_markup()

    paginator = Paginator(services, page=page)

    if not paginator.get_page():
        page = paginator.pages
        paginator = Paginator(services, page=page)

    service = paginator.get_page()[0]

    caption = (
        f"🛠 <b>Услуга: {service.name}</b>\n"
        f"────────────────────\n"
        f"💰 Цена: {service.price} руб.\n\n"
        f"📝 <i>{service.description}</i>"
    )

    media = types.InputMediaPhoto(
        media=service.image,
        caption=caption,
        parse_mode="HTML"
    )
    kb_builder = get_services_btns(
        level=level,
        page=page,
        service=service,
        pagination_btns=pages(paginator)
    )

    kb = InlineKeyboardBuilder()

    kb.row(types.InlineKeyboardButton(text='➕ Добавить услугу',
                                      callback_data=ClickService(pref="add_service", category_id=category_id).pack()))
    kb.row(types.InlineKeyboardButton(text='🔙 К категориям',
                                      callback_data=MenuCallBackAdmin(level=2, menu_name='category').pack()))
    kb.adjust(*(2,))
    kb_builder.attach(kb)

    return media, kb_builder.as_markup()


def get_services_btns(
    *,
    page: int,
    level: int,
    service: object,
    pagination_btns: dict,
    sizes: tuple[int] = (2,),
):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(
        InlineKeyboardButton(text="🗑 Удалить", callback_data=ClickService(
            service_id=service.id,
            category_id=service.category_id,
            pref="delete",
            page=page).pack()),
        InlineKeyboardButton(text="✏️ Изменить", callback_data=ClickService(
            service_id=service.id,
            category_id=service.category_id,
            pref="update",
            page=page).pack()),
    )

    keyboard.adjust(*sizes)

    nav_row = []
    for text, action in pagination_btns.items():
        target_page = page + 1 if action == "next" else page - 1

        nav_row.append(InlineKeyboardButton(
            text=text,
            callback_data=MenuCallBackAdmin(
                level=level,
                menu_name="services",
                category_id=service.category_id,
                page=target_page
            ).pack()
        ))

    if nav_row:
        keyboard.row(*nav_row)

    return keyboard


async def edit_smart(message: types.Message, msg_id: int, text: str, keyboard=None):
    if keyboard:
        kb = keyboard
    else:
        kb = InlineKeyboardBuilder().button(
            text="❌ Отмена", callback_data="cancel_add_service").as_markup()

    try:

        await message.bot.edit_message_text(chat_id=message.chat.id, message_id=msg_id, text=text, reply_markup=kb, parse_mode="Markdown")
    except TelegramBadRequest:
        try:
            await message.bot.edit_message_caption(chat_id=message.chat.id, message_id=msg_id, caption=text, reply_markup=kb, parse_mode="Markdown")
        except TelegramBadRequest:
            pass


@service_router_for_admin.callback_query(ClickService.filter(F.pref == "delete"))
async def ask_service(callback: types.CallbackQuery, callback_data: ClickService, session: AsyncSession):
    kb = InlineKeyboardBuilder()

    kb.add(InlineKeyboardButton(
        text="✅ Да, удалить", callback_data=ClickService(
            pref="confirm_delete", category_id=callback_data.category_id, service_id=callback_data.service_id,  service_name=callback_data.service_name, page=callback_data.page
        ).pack()),
        InlineKeyboardButton(
        text="❌ Отмена", callback_data=MenuCallBackAdmin(
            level=3, menu_name="services", category_id=callback_data.category_id, page=callback_data.page
        ).pack()))
    text = f"⚠️ Удалить услугу: {callback_data.service_name}?"
    try:

        await callback.message.edit_caption(caption=text, reply_markup=kb.as_markup())
    except TelegramBadRequest:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=kb.as_markup())


@service_router_for_admin.callback_query(ClickService.filter(F.pref == "confirm_delete"))
async def delete_service(callback: types.CallbackQuery, callback_data: ClickService, session: AsyncSession):

    await orm_delete_service_by_id(session=session, service_id=callback_data.service_id)

    await session.commit()
    await callback.answer("Удалено")

    from .menu_processing import get_menu_content_for_admin

    content, reply_markup = await get_menu_content_for_admin(
        session=session, level=3, menu_name="services", page=callback_data.page, category_id=callback_data.category_id
    )

    if isinstance(content, types.InputMediaPhoto):
        try:

            await callback.message.edit_media(media=content, reply_markup=reply_markup)

        except TelegramBadRequest:
            await callback.message.delete()
            await callback.message.answer_photo(photo=content.media, caption=content.caption, reply_markup=reply_markup)
    else:

        try:
            await callback.message.edit_text(text=content, reply_markup=reply_markup)

        except TelegramBadRequest:
            await callback.message.delete()
            await callback.message.answer(text=content, reply_markup=reply_markup)


@service_router_for_admin.callback_query(ClickService.filter(F.pref == "add_service"))
async def start_add_service(callback: types.CallbackQuery, callback_data: ClickService, session: AsyncSession, state: FSMContext):
    await state.update_data(msg_to_edit=callback.message.message_id, return_page=callback_data.page, old_category_id=callback_data.category_id)
    await state.set_state(AddService.name)

    text = "📝 **Режим добавления**\n_____________________\nВведите название для новой услуги:"
    kb = InlineKeyboardBuilder().button(
        text="❌ Отмена", callback_data="cancel_add_service").as_markup()

    try:

        url = "https://upload.wikimedia.org/wikipedia/commons/2/28/Beelden_in_Leiden_2016_04_crop.jpg"

        media = InputMediaPhoto(
            media=url,
            caption=text,
            parse_mode="Markdown"
        )

        await callback.message.edit_media(media=media, reply_markup=kb)

    except TelegramBadRequest:
        try:
            await callback.message.delete()
            new_msg = await callback.message.answer_photo(photo=url, caption=text, reply_markup=kb)
            await state.update_data(msg_to_edit=new_msg.message_id)

        except TelegramBadRequest:
            new_msg = await callback.message.answer_photo(photo=url, caption=text, reply_markup=kb)
            await state.update_data(msg_to_edit=new_msg.message_id)


@service_router_for_admin.callback_query(F.data == "cancel_add_service")
async def cancel_add_service(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    page = data.get("return_page", 1)
    category_id = data.get("old_category_id") or data.get("category")
    msg_id = data.get("msg_to_edit")

    await state.clear()

    from .menu_processing import get_menu_content_for_admin
    content, reply_markup = await get_menu_content_for_admin(
        session=session, level=3, menu_name="services", category_id=category_id, page=page
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


@service_router_for_admin.message(AddService.name, or_f(F.text == ".", F.text))
async def add_service_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    service_id = data.get("old_service_id", None)
    msg_id = data.get("msg_to_edit")

    await message.delete()

    if message.text == "." and service_id:
        new_name = data.get("old_name")
    else:
        if not (3 <= len(message.text) <= 30):
            error_text = (
                f"❌ **Ошибка: слишком {'короткое' if len(message.text) < 3 else 'длинное'} название!**\n"
                f"Должно быть от 3 до 30 символов (сейчас: {len(message.text)})\n\n"
                f"Введите название заново {'или "."' if service_id else ''}:"
            )
            return await edit_smart(message, msg_id, error_text)
        new_name = message.text

    await state.update_data(name=new_name)
    await state.set_state(AddService.description)

    next_text = f"✅ Название: **{new_name}**\n\n📝 Теперь введите **описание** услуги {'или "."' if service_id else ''}:"
    await edit_smart(message, msg_id, next_text)


@service_router_for_admin.message(AddService.description, or_f(F.text == ".", F.text))
async def add_service_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg_id = data.get("msg_to_edit")
    service_id = data.get("old_service_id", None)

    await message.delete()

    if message.text == "." and service_id:
        new_description = data.get("old_description")
    else:
        if len(message.text) >= 300:
            error_text = (
                f"❌ **Ошибка: слишком длинное описание!**\n"
                f"Должно быть до 300 символов (сейчас: {len(message.text)})\n\n"
                f"Введите описание заново {'или "."' if service_id else ''}:"
            )
            return await edit_smart(message=message, msg_id=msg_id, text=error_text)
        new_description = message.text

    await state.update_data(description=new_description)
    await state.set_state(AddService.price)

    next_text = (
        f"✅ Описание принято.\n\n"
        f"💰 Теперь введите **цену** услуги (число) {'. если оставить прежнюю' if service_id else ''}:"
    )
    await edit_smart(message, msg_id, next_text)


@service_router_for_admin.message(AddService.price, or_f(F.text == ".", F.text))
async def add_service_price(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    msg_id = data.get("msg_to_edit")
    service_id = data.get("old_service_id")
    category_id = data.get("old_category_id")

    await message.delete()

    if message.text == "." and service_id:
        price_val = data.get("old_price")
    else:

        try:
            price_text = message.text.replace(" ", "").replace(",", ".")
            price_val = Decimal(price_text)

            max_val = Decimal("9999999")
            min_val = Decimal("0")

            if not (min_val <= price_val <= max_val) or len(price_text) > 10:
                reason = " больше лимита" if price_val > max_val else " меньше нуля"
                if len(price_text) > 10:
                    reason = " слишком длинное"

                error_text = (
                    f"❌ **Ошибка: Число{reason} ₽**\n"
                    f"Допустимо: от **0** до **9 999 999** ₽\n\n"
                    f"Введите цену заново{' или \".\"' if service_id else ''}:"
                )
                return await edit_smart(message=message, msg_id=msg_id, text=error_text)

        except (InvalidOperation, ValueError):
            error_text = "❌ **Ошибка!** Введите корректное число (например: 500 или 1250.50):"
            return await edit_smart(message=message, msg_id=msg_id, text=error_text)

    await state.update_data(price=float(price_val))

    if category_id:
        await state.set_state(AddService.image)
        next_text = (
            f"✅ Цена: **{price_val:,} руб.**\n\n".replace(",", " ") +
            f"📸 Отправьте **фотографию** услуги{' или \".\" чтобы оставить текущую' if service_id else ''}:"
        )
        await edit_smart(message, msg_id, next_text)
    else:

        await state.set_state(AddService.category)

        categories = await orm_get_categories(session=session)

        if not categories:
            await edit_smart(message, msg_id, "❌ Сначала создайте хотя бы одну категорию!")
            return

        kb_builder = InlineKeyboardBuilder()
        for cat in categories:

            kb_builder.button(
                text=cat.name,
                callback_data=f"fsm_cat_{cat.id}"
            )

        kb_builder.adjust(2)

        kb_builder.row(types.InlineKeyboardButton(
            text="❌ Отмена", callback_data="cancel_add_service"))

        next_text = (
            f"✅ Цена: **{price_val:,} руб.**\n\n".replace(",", " ") +
            "📂 Выберите **категорию** для этой услуги:"
        )

        await edit_smart(
            message=message,
            msg_id=msg_id,
            text=next_text,
            keyboard=kb_builder.as_markup()
        )


@service_router_for_admin.callback_query(AddService.category, F.data.startswith("fsm_cat_"))
async def add_service_category_choice(callback: types.CallbackQuery, state: FSMContext):

    category_id = int(callback.data.replace("fsm_cat_", ""))

    await state.update_data(category=category_id)
    await state.set_state(AddService.image)

    text = "📂 Категория выбрана.\n\n📸 Теперь отправьте **фотографию** услуги:"

    await edit_smart(callback.message, callback.message.message_id, text)
    await callback.answer()


@service_router_for_admin.message(AddService.image, F.photo)
async def add_service_image(message: types.Message, state: FSMContext, session: AsyncSession):

    photo_id = message.photo[-1].file_id
    data = await state.get_data()

    await state.update_data(image=photo_id)

    await message.delete()
    await proceed_to_save(message, state, session)


@service_router_for_admin.message(AddService.image, F.text == ".")
async def skip_service_image(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()

    if not data.get("old_service_id"):

        return await edit_smart(message, data.get("msg_to_edit"), "❌ Для новой услуги фото обязательно! Отправьте изображение:")

    await state.update_data(image=data.get("old_image"))
    await message.delete()
    await proceed_to_save(message, state, session)


async def proceed_to_save(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()

    msg_id = data.get("msg_to_edit")
    service_id = data.get("old_service_id")
    data_sent = {
        "name": data.get("name"),
        "description": data.get("description"),
        "price": float(data.get("price")),
        "image": data.get("image"),
        "category": int(data.get("category") or data.get("old_category_id"))
    }

    try:
        if service_id:
            await orm_update_service_by_id(session, service_id, data_sent)
            text = "✅ Услуга успешно обновлена!"

        else:
            await orm_add_service(session, data_sent)
            text = "✅ Услуга успешно добавлена!"

        await session.commit()
        await state.clear()

        kb = InlineKeyboardBuilder().button(text="🔙 К списку услуг", callback_data=MenuCallBackAdmin(level=3,
                                                                                                     menu_name="services", category_id=data.get("old_category_id", data.get("category")), page=1)).as_markup()

        await edit_smart(message, msg_id, text, keyboard=kb)

    except Exception as e:
        print(e)
        await session.rollback()
        await edit_smart(message, msg_id, f"❌ Ошибка при сохранении.")


@service_router_for_admin.callback_query(ClickService.filter(F.pref == "update"))
async def start_update_service(callback: types.CallbackQuery, callback_data: ClickService, session: AsyncSession, state: FSMContext):

    service = await orm_get_service_by_id(session, callback_data.service_id)

    await state.update_data(
        old_service_id=service.id,
        old_name=service.name,
        old_description=service.description,
        old_price=service.price,
        old_image=service.image,
        old_category_id=service.category_id,
        msg_to_edit=callback.message.message_id,
        return_page=callback_data.page
    )

    await state.set_state(AddService.name)
    text = f"✏️ **Редактирование: {service.name}**\n\nВведите новое название или '.' чтобы оставить прежнее:"

    await callback.message.edit_caption(
        caption=text,
        reply_markup=InlineKeyboardBuilder().button(
            text="❌ Отмена", callback_data="cancel_add_service").as_markup()
    )
