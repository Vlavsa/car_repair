from aiogram import F, types, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession


from database.Client import orm_check_client, orm_add_client\

from database.Orders import orm_add_to_order
from filters.chat_types import ChatTypeFilter

from kbds.inline.main_menu import MenuCallBack

from handlers.private_chat.query_users.menu_processing import check_image_for_menu, get_menu_content
from handlers.private_chat.query_users.Order import order_user_router
from handlers.private_chat.query_users.state import AddClient

user_router = Router()
user_router.message.filter(ChatTypeFilter(["private"]))


user_router.include_routers(
    order_user_router
)


@user_router.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext, session: AsyncSession):
    user = await orm_check_client(session=session, client_id=message.from_user.id)

    if user:
        await check_image_for_menu(message=message, session=session)
    else:
        kb = ReplyKeyboardBuilder()
        kb.add(types.KeyboardButton(
            text="Отправить номер телефона", request_contact=True))

        await message.answer(
            f"Привет, {message.from_user.first_name}! Для регистрации необходимо поделиться номером телефона.",
            reply_markup=kb.as_markup(
                resize_keyboard=True, one_time_keyboard=True),
            parse_mode="HTML"  # Вынесли из as_markup
        )
        await state.set_state(AddClient.wait_phone)


@user_router.message(AddClient.wait_phone, F.contact)
async def get_phone(message: types.Message, state: FSMContext, session: AsyncSession):
    await orm_add_client(
        session=session,
        id_client=message.from_user.id,
        name=message.from_user.first_name,
        username=message.from_user.username or "hidden",
        phone_number=message.contact.phone_number
    )

    data = await state.get_data()
    temp_list = data.get("list_services", [])

    if temp_list:
        for service_id in temp_list:
            await orm_add_to_order(
                session=session,
                client_id=message.from_user.id,
                service_id=service_id,
                status_id=1
            )

    await state.clear()

    await message.answer(
        "✨ Регистрация завершена! Ваши выбранные услуги сохранены в корзине.",
        reply_markup=types.ReplyKeyboardRemove()
    )

    await check_image_for_menu(message=message, session=session)


@user_router.callback_query(MenuCallBack.filter(~F.menu_name.in_(["add_to_order", "reduce_from_order"])))
async def user_menu(callback: types.CallbackQuery, callback_data: MenuCallBack, session: AsyncSession, state: FSMContext):

    media, replay_markup = await get_menu_content(
        session,
        level=callback_data.level,
        menu_name=callback_data.menu_name,
        category=callback_data.category,
        page=callback_data.page,
        state=state
    )

    try:

        if callback.message.text and isinstance(media, types.InputMediaPhoto):
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=media.media,
                caption=media.caption,
                reply_markup=replay_markup,
                parse_mode="HTML"
            )

        elif callback.message.photo and isinstance(media, types.InputMediaPhoto):
            media.parse_mode = "HTML"
            await callback.message.edit_media(
                media=media,
                reply_markup=replay_markup
            )

        elif callback.message.photo and not isinstance(media, types.InputMediaPhoto):
            await callback.message.delete()

            text_content = media if isinstance(
                media, str) else f"🛠 {media.name}\n\n{media.description}"
            await callback.message.answer(
                text=text_content,
                reply_markup=replay_markup,
                parse_mode="HTML"
            )

        else:
            text_content = media if isinstance(
                media, str) else f"🛠 {media.name}\n\n{media.description}"
            await callback.message.edit_text(
                text=text_content,
                reply_markup=replay_markup,
                parse_mode="HTML"
            )

    except TelegramBadRequest as e:
        if "message is not modified" in e.message:

            pass
        else:

            raise e

    await callback.answer()
