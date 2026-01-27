from aiogram import F, Router, types


from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext


from kbds.inline import get_callback_btns
from kbds.reply import get_keyboard, ADMIN_KB

from sqlalchemy.ext.asyncio import AsyncSession

from filters.chat_type import ChatTypeFilter, IsAdmin

from database.Service import (
    orm_add_service,
    orm_delete_service,
    orm_get_service,
    orm_get_services,
    orm_update_service,
)





service_router_for_admin = Router()
service_router_for_admin.message.filter(ChatTypeFilter(["private"]), IsAdmin())


class AddService(StatesGroup):
    # Шаги состояний
    name = State()
    description = State()
    price = State()
    image = State()

    service_for_change = None

    texts = {
        "AddService:name": "Введите название заново:",
        "AddService:description": "Введите описание заново:",
        "AddService:price": "Введите стоимость заново:",
        "AddService:image": "Этот стейт последний, поэтому...",
    }



@service_router_for_admin.message(F.text == "Ассортимент")
async def starring_at_product(message: types.Message, session: AsyncSession):
    for product in await orm_get_services(session):
        await message.answer_photo(
            product.image,
            caption=f"<strong>{product.name}\
                    </strong>\n{product.description}\nСтоимость: {round(product.price, 2)}",
            reply_markup=get_callback_btns(
                btns={
                    "Удалить": f"delete_{product.id}",
                    "Изменить": f"change_{product.id}",
                }
            ),
        )
    await message.answer("ОК, вот список услуг ⏫")


@service_router_for_admin.callback_query(F.data.startswith("delete_"))
async def delete_service_callback(callback: types.CallbackQuery, session: AsyncSession):
    product_id = callback.data.split("_")[-1]
    await orm_delete_service(session, int(product_id))

    await callback.answer("Услуга удалена")
    await callback.message.answer("Услуга удалена!")

# FSM:

# Становимся в состояние ожидания ввода name
@service_router_for_admin.callback_query(StateFilter(None), F.data.startswith("change_"))
async def change_service_callback(
    callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
):
    service_id = callback.data.split("_")[-1]

    service_for_change = await orm_get_service(session, int(service_id))

    AddService.service_for_change = service_for_change

    await callback.answer()
    await callback.message.answer(
        "Введите название услуги", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddService.name)


# Становимся в состояние ожидания ввода name
@service_router_for_admin.message(StateFilter(None), F.text == "Добавить услугу")
async def add_service(message: types.Message, state: FSMContext):
    
    await message.answer(
        "Введите название услуги", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddService.name)


# Хендлер отмены и сброса состояния должен быть всегда именно хдесь,
# после того как только встали в состояние номер 1 (элементарная очередность фильтров)
@service_router_for_admin.message(StateFilter("*"), Command("отмена"))
@service_router_for_admin.message(StateFilter("*"), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    if AddService.service_for_change:
        AddService.service_for_change = None
    await state.clear()

    from ....kbds.reply import ADMIN_KB
    await message.answer("Действия отменены", reply_markup=ADMIN_KB)


# Вернутся на шаг назад (на прошлое состояние)
@service_router_for_admin.message(StateFilter("*"), Command("назад"))
@service_router_for_admin.message(StateFilter("*"), F.text.casefold() == "назад")
async def back_step_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()

    if current_state == AddService.name:
        await message.answer(
            'Предыдущего шага нет, или введите название товара или напишите "отмена"'
        )
        return

    previous = None
    for step in AddService.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(
                f"Ок, вы вернулись к прошлому шагу \n {AddService.texts[previous.state]}"
            )
            return
        previous = step


# Ловим данные для состояние name и потом меняем состояние на description
@service_router_for_admin.message(AddService.name, or_f(F.text, F.text == "."))
async def add_name(message: types.Message, state: FSMContext):
    if message.text == ".":
        await state.update_data(name=AddService.service_for_change.name)
    else:
        # Здесь можно сделать какую либо дополнительную проверку
        # и выйти из хендлера не меняя состояние с отправкой соответствующего сообщения
        # например:
        if len(message.text) >= 100:
            await message.answer(
                "Название услуги не должно превышать 100 символов. \n Введите заново"
            )
            return

        await state.update_data(name=message.text)
    await message.answer("Введите описание услуги")
    await state.set_state(AddService.description)


# Хендлер для отлова некорректных вводов для состояния name
@service_router_for_admin.message(AddService.name)
async def add_name2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели не допустимые данные, введите текст названия услуги")


# Ловим данные для состояние description и потом меняем состояние на price
@service_router_for_admin.message(AddService.description, or_f(F.text, F.text == "."))
async def add_description(message: types.Message, state: FSMContext):
    if message.text == ".":
        await state.update_data(description=AddService.service_for_change.description)
    else:
        await state.update_data(description=message.text)
    await message.answer("Введите стоимость услуги")
    await state.set_state(AddService.price)


# Хендлер для отлова некорректных вводов для состояния description
@service_router_for_admin.message(AddService.description)
async def add_description2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели не допустимые данные, введите текст описания услуги")


# Ловим данные для состояние price и потом меняем состояние на image
@service_router_for_admin.message(AddService.price, or_f(F.text, F.text == "."))
async def add_price(message: types.Message, state: FSMContext):
    if message.text == ".":
        await state.update_data(price=AddService.service_for_change.price)
    else:
        try:
            float(message.text)
        except ValueError:
            await message.answer("Введите корректное значение цены")
            return

        await state.update_data(price=message.text)
    await message.answer("Загрузите изображение товара")
    await state.set_state(AddService.image)


# Хендлер для отлова некорректных ввода для состояния price
@service_router_for_admin.message(AddService.price)
async def add_price2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели не допустимые данные, введите стоимость услуги")


# Ловим данные для состояние image и потом выходим из состояний
@service_router_for_admin.message(AddService.image, or_f(F.photo, F.text == "."))
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text and message.text == ".":
        await state.update_data(image=AddService.service_for_change.image)

    else:
        await state.update_data(image=message.photo[-1].file_id)
    data = await state.get_data()
    try:
        if AddService.service_for_change:
            await orm_update_service(session, AddService.service_for_change.id, data)
        else:
            await orm_add_service(session, data)


        await message.answer("Услуга добавлена/изменена", reply_markup=ADMIN_KB)
        await state.clear()

    except Exception as e:
        await message.answer(
            f"Ошибка: \n{str(e)}\nОбратись к программеру, он опять денег хочет",
            reply_markup=ADMIN_KB,
        )
        await state.clear()

    AddService.service_for_change = None


@service_router_for_admin.message(AddService.image)
async def add_image2(message: types.Message, state: FSMContext):
    await message.answer("Отправьте фото услуги")