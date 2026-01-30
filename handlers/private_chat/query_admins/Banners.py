from aiogram import F, Router, types


from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext


from kbds.inline.inline import get_callback_btns
from kbds.reply import get_keyboard, ADMIN_KB

from sqlalchemy.ext.asyncio import AsyncSession

from filters.chat_types import ChatTypeFilter, IsAdmin

from database.Banner import (
    orm_add_banner_description,
    orm_change_banner_image,
    orm_get_banner,
    orm_get_info_pages
)



banner_router_for_admin = Router()
banner_router_for_admin.message.filter(ChatTypeFilter(["private"]), IsAdmin())


################# Микро FSM для загрузки/изменения баннеров ############################

class AddBanner(StatesGroup):
    image = State()

# Отправляем перечень информационных страниц бота и становимся в состояние отправки photo
@banner_router_for_admin.message(StateFilter(None), F.text == 'Добавить/Изменить баннер')
async def add_image2(message: types.Message, state: FSMContext, session: AsyncSession):
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    await message.answer(f"Отправьте фото баннера.\nВ описании укажите для какой страницы:\
                         \n{', '.join(pages_names)}")
    await state.set_state(AddBanner.image)

# Добавляем/изменяем изображение в таблице (там уже есть записанные страницы по именам:
# main, catalog, cart(для пустой корзины), about, payment, shipping
@banner_router_for_admin.message(AddBanner.image, F.photo)
async def add_banner(message: types.Message, state: FSMContext, session: AsyncSession):
    image_id = message.photo[-1].file_id
    for_page = message.caption.strip()
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    if for_page not in pages_names:
        await message.answer(f"Введите нормальное название страницы, например:\
                         \n{', '.join(pages_names)}")
        return
    await orm_change_banner_image(session, for_page, image_id,)
    await message.answer("Баннер добавлен/изменен.", reply_markup=ADMIN_KB)
    await state.clear()

# ловим некоррекный ввод
@banner_router_for_admin.message(AddBanner.image)
async def add_banner2(message: types.Message, state: FSMContext):
    await message.answer("Отправьте фото баннера или отмена")

