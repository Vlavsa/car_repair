from aiogram import F, types, Router
from aiogram.filters import CommandStart

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession


from database.Client import orm_check_client, orm_add_client\

from filters.chat_types import ChatTypeFilter

from kbds.inline.main_menu import MenuCallBack

from handlers.private_chat.query_users.menu_processing import check_image_for_menu, get_menu_content

user_router = Router()
user_router.message.filter(ChatTypeFilter(["private"]))


class AddClient(StatesGroup):
    # Шаги состояний
    name = State()
    wait_phone = State()


@user_router.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext, session: AsyncSession):
    # Проверяем, есть ли уже такой клиент
    user = await orm_check_client(session=session, client_id=message.from_user.id)

    if user:
        await check_image_for_menu(message=message, session=session)
        await state.clear()
    else:
        # Создаем кнопку запроса контакта
        kb = ReplyKeyboardBuilder()
        kb.add(types.KeyboardButton(
            text="Отправить номер телефона", request_contact=True))

        await message.answer(
            f"Привет, {message.from_user.first_name}! Для регистрации необходимо поделиться номером телефона.",
            reply_markup=kb.as_markup(
                resize_keyboard=True, one_time_keyboard=True)
        )
        await state.set_state(AddClient.wait_phone)


@user_router.message(AddClient.wait_phone, F.contact)
async def get_phone(message: types.Message, state: FSMContext, session: AsyncSession):
    contact = message.contact
    await orm_add_client(
        session=session,
        id_client=message.from_user.id,
        name=message.from_user.first_name,
        username=message.from_user.username or "hidden",
        phone_number=contact.phone_number
    )
    await state.clear()  # Не забудьте очистить состояние после регистрации

    await message.answer(
        "Регистрация завершена!",
        reply_markup=types.ReplyKeyboardRemove()  # Убираем кнопку контакта
    )
    await check_image_for_menu(message=message, session=session)


@user_router.callback_query(MenuCallBack.filter())
async def user_menu(callback: types.CallbackQuery, callback_data: MenuCallBack, session: AsyncSession):

    media, replay_markup = await get_menu_content(
        session,
        level=callback_data.level,
        menu_name=callback_data.menu_name,
        category=callback_data.category,
        page=callback_data.page,
    )

    if callback.message.text and isinstance(media, types.InputMediaPhoto):
        await callback.message.delete()  # Удаляем старый текст
        await callback.message.answer_photo(  # Отправляем новое фото
            photo=media.media,
            caption=media.caption,
            reply_markup=replay_markup
        )

    elif callback.message.photo and isinstance(media, types.InputMediaPhoto):
        await callback.message.edit_media(
            media=media,  # Передаем объект целиком
            reply_markup=replay_markup
        )

    elif callback.message.photo and not isinstance(media, types.InputMediaPhoto):
        await callback.message.delete()  # Удаляем фото
        await callback.message.answer(   # Отправляем чистый текст
            text=f"🖼 (Изображение отсутствует для {media.name})\n\n{media.description}",
            reply_markup=replay_markup
        )

    else:
        await callback.message.edit_text(
            text=f"🖼 (Изображение отсутствует для {media.name})\n\n{media.description}",
            reply_markup=replay_markup
        )

    await callback.answer()
