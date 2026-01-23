from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from sqlalchemy.ext.asyncio import AsyncSession


from database.orm_query import (
    orm_add_service, 
    orm_get_service, 
    orm_get_services, 
    orm_update_service, 
    orm_delete_service)


from filters.filters_type import ChatTypeFilter, IsAdmin
from kbds.inline import get_callback_btns
from kbds.replay import get_keyboard


admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())


ADMIN_KB = get_keyboard(
    "Добавить услугу",
    "Ассортимент",
    placeholder="Выберите действие",
    sizes=(2,),
)

# Код ниже для машины состояний (FSM)


class AddService(StatesGroup):
    name = State()
    description = State()
    price = State()
    image = State()

    texts = {
        'AddService:name': 'Введите название заново:',
        'AddService:description': 'Введите описание заново:',
        'AddService:price': 'Введите цену заново:',
        'AddService:image': 'Это последний пункт...',
    }

# Активировать администратора


@admin_router.message(Command("admin"))
async def admin_features(message: types.Message, state: FSMContext):
    await message.answer("Что хотите сделать?", reply_markup=ADMIN_KB)


@admin_router.message(F.text == "Ассортимент")
async def starring_at_service(message: types.Message, session: AsyncSession):
    await message.answer("ОК, вот список 'Услуг'")
    for service in await orm_get_services(session=session):
        await message.answer_photo(
            service.image,
            caption=f"<strong>{service.name}\
                    </strong>\n{service.description}\nСтоимость: {round(service.price, 2)}",
            reply_markup=get_callback_btns(
                    btns = {
                        'Удалить': f'delete_{service.id}',
                        'Изменить': f'charge_{service.id}',
                    }
            )
        )

@admin_router.callback_query(F.data.startswith("delete_"))
async def delete_service_callback(callback: types.CallbackQuery, session: AsyncSession):
    service_id = callback.data.split("_")[-1]
    await orm_delete_service(session, int(service_id))

    await callback.answer("Услуга удалена")
    await callback.message.answer("Услуга удалена!")



# Состояние нашего класса Services
@admin_router.message(StateFilter(None), F.text == "Добавить услугу")
async def add_service(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите название: ", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddService.name)

# Посмотреть как записывается состояние(отправляет в телегу)
    data = await state.get_data()
    await message.answer(str(data))


# Становимся в состояние ожидания ввода name
@admin_router.callback_query(StateFilter(None), F.data.startswith("change_"))
async def change_product_callback(
    callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
):
    product_id = callback.data.split("_")[-1]

    product_for_change = await orm_get_service(session, int(product_id))

    AddService.product_for_change = product_for_change

    await callback.answer()
    await callback.message.answer(
        "Введите название товара", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddService.name)


# Хендлер отмены и сброса состояния должен быть всегда именно хдесь,
# после того как только встали в состояние номер 1 (элементарная очередность фильтров)
@admin_router.message(StateFilter('*'), Command("отмена"))
@admin_router.message(StateFilter('*'), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:

    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KB)


# Вернутся на шаг назад (на прошлое состояние)
@admin_router.message(StateFilter('*'), Command("назад"))
@admin_router.message(StateFilter('*'), F.text.casefold() == "назад")
async def back_step_handler(message: types.Message, state: FSMContext) -> None:

    current_state = await state.get_state()

    if current_state == AddService.name:
        await message.answer('Предидущего шага нет, или введите название товара или напишите "отмена"')
        return

    previous = None
    for step in AddService.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f"Ок, вы вернулись к прошлому шагу \n {AddService.texts[previous.state]}")
            return
        previous = step


@admin_router.message(AddService.name, F.text)
async def add_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите описание: ")
    await state.set_state(AddService.description)

# Посмотреть как записывается состояние(отправляет в телегу)
    data = await state.get_data()
    await message.answer(str(data))


@admin_router.message(AddService.name)
async def add_name2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, введите текст название товара: ")


@admin_router.message(AddService.description, F.text)
async def add_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите стоимость: ")
    await state.set_state(AddService.price)

# Посмотреть как записывается состояние(отправляет в телегу)
    data = await state.get_data()
    await message.answer(str(data))


@admin_router.message(AddService.description)
async def add_descriptio2n(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, введите текст описания товара: ")


@admin_router.message(AddService.price, F.text)
async def add_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("Загрузите изображение: ")
    await state.set_state(AddService.image)

# Посмотреть как записывается состояние(отправляет в телегу)
    data = await state.get_data()
    await message.answer(str(data))


@admin_router.message(AddService.price)
async def add_price2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, введите цифрами цену товара: ")


@admin_router.message(AddService.image, F.photo)
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(image=message.photo[-1].file_id)

    data = await state.get_data()
    # try:
    await orm_add_service(session=session, data=data)
    await message.answer("'Услуга' добавлена", reply_markup=ADMIN_KB)
    await state.clear()

    # except Exception as e:
    #     await message.answer(
    #         f'Ошибка: \n {str(e)}\n Спроси у Влада, он не доделал'
    #     )
    #     await state.clear()


@admin_router.message(AddService.image)
async def add_image2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, загрузите фото товара: ")
