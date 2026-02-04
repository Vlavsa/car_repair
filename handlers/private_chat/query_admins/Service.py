from aiogram import F, Router, types


from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext


from kbds.inline.categories_admin import CategoryClick
from kbds.inline.inline import get_callback_btns, button_service_admin, button_categories_admin
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
    orm_get_categories_inner_join_services
)


service_router_for_admin = Router()
service_router_for_admin.message.filter(ChatTypeFilter(["private"]), IsAdmin())


@service_router_for_admin.callback_query(F.data == 'prev_category')
async def prev_menu_2(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    await callback.message.edit_text(
        text="Настройка категорий:",
        reply_markup=button_categories_admin)


@service_router_for_admin.message(F.text == 'Ассортимент')
async def admin_features(message: types.Message, session: AsyncSession):
    categories = await orm_get_categories(session)
    btns = {category.name: f'category_{category.id}' for category in categories}
    await message.answer("Выберите категорию", reply_markup=get_callback_btns(btns=btns, sizes=(2, 2,)))


@service_router_for_admin.callback_query(CategoryClick.filter(F.action == "category_"))
async def starring_at_service(callback: types.CallbackQuery, session: AsyncSession, callback_data: CategoryClick):
    category_id = callback_data.category_id
    query = await orm_get_services_by_category_id(session=session, category_id=int(category_id))

    if not query or len(query) < 1:
        await callback.answer()
        await callback.message.answer('Список пуст....', reply_markup=button_service_admin)

    await callback.message.delete()
    await callback.answer()

    for service in query:
        await callback.message.answer_photo(
            service.image,
            caption=f"<strong>{service.name}\
                    </strong>\n{service.description}\nСтоимость: {round(service.price, 2)}",
            reply_markup=get_callback_btns(
                btns={
                    "Удалить": f"delete_{service.id}",
                    "Изменить": f"change_{service.id}",
                },
                sizes=(2,)
            ),
        )
    await callback.answer()
    await callback.message.answer("ОК, вот список товаров ⏫", reply_markup=button_service_admin)


@service_router_for_admin.callback_query(F.data.startswith("delete_"))
async def delete_service_callback(callback: types.CallbackQuery, session: AsyncSession):
    product_id = callback.data.split("_")[-1]
    await orm_delete_service_by_id(session, int(product_id))

    await callback.answer("Услуга удалена")
    await callback.message.answer("Услуга удалена!")
    return await callback.message.delete()


######################### FSM для дабавления/изменения товаров админом ###################
class AddService(StatesGroup):
    # Шаги состояний
    name = State()
    description = State()
    category = State()
    price = State()
    image = State()

    service_for_change = None

    texts = {
        "AddService:name": "Введите название заново:",
        "AddService:description": "Введите описание заново:",
        "AddService:price": "Введите стоимость заново:",
        "AddService:image": "Этот стейт последний, поэтому...",
    }

# Становимся в состояние ожидания ввода name


@service_router_for_admin.callback_query(StateFilter(None), F.data.startswith("change_"))
async def change_service_callback(
    callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
):
    service_id = callback.data.split("_")[-1]

    service_for_change = await orm_get_service_by_id(session, int(service_id))

    AddService.service_for_change = service_for_change

    await callback.answer()
    await callback.message.answer(
        "Введите название услуги", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddService.name)


# Становимся в состояние ожидания ввода name
@service_router_for_admin.callback_query(F.data == "add_service")
async def add_service(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
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
async def add_description(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text == "." and AddService.service_for_change:
        await state.update_data(description=AddService.service_for_change.description)
    else:
        if 4 >= len(message.text) >= 150:
            await message.answer(
                "Название товара не должно превышать 150 символов\nили быть менее 5ти символов. \n Введите заново"
            )
            return
        else:
            await state.update_data(description=message.text)

    categories = await orm_get_categories(session=session)
    btns = {category.name: str(category.id) for category in categories}
    await message.answer("Выберите категорию", reply_markup=get_callback_btns(btns=btns))
    await state.set_state(AddService.category)
    await state.set_state(AddService.category)


# Хендлер для отлова некорректных вводов для состояния description
@service_router_for_admin.message(AddService.description)
async def add_description2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели не допустимые данные, введите текст описания услуги")

# Ловим callback выбора категории


@service_router_for_admin.callback_query(AddService.category)
async def category_choice(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    if int(callback.data) in [category.id for category in await orm_get_categories(session)]:
        await callback.answer()
        await state.update_data(category=callback.data)
        await callback.message.answer('Теперь введите цену услуги.')
        await state.set_state(AddService.price)
    else:
        await callback.message.answer('Выберите катеорию из кнопок.')
        await callback.answer()

# Ловим любые некорректные действия, кроме нажатия на кнопку выбора категории


@service_router_for_admin.message(AddService.category)
async def category_choice2(message: types.Message, state: FSMContext):
    await message.answer("'Выберите катеорию из кнопок.'")


# Ловим данные для состояние price и потом меняем состояние на image
@service_router_for_admin.message(AddService.price, or_f(F.text, F.text == "."))
async def add_price(message: types.Message, state: FSMContext):
    price = message.text.replace(" ", "")
    if price == "." and AddService.service_for_change:
        await state.update_data(price=AddService.service_for_change.price)
    else:
        try:
            float(price)
        except ValueError:
            await message.answer("Введите корректное значение цены")
            return

        await state.update_data(price=price)
    if float(price) > 999999:
        await message.answer("Число не может быть больше 999 999")
        return
    await message.answer("Загрузите изображение товара")
    await state.set_state(AddService.image)


# Хендлер для отлова некорректных ввода для состояния price
@service_router_for_admin.message(AddService.price)
async def add_price2(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели не допустимые данные, введите стоимость услуги")


# Ловим данные для состояние image и потом выходим из состояний
@service_router_for_admin.message(AddService.image, or_f(F.photo, F.text == "."))
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text and message.text == "." and AddService.service_for_change:
        await state.update_data(image=AddService.service_for_change.image)

    elif message.photo:
        await state.update_data(image=message.photo[-1].file_id)
    else:
        await message.answer("Отправьте фото услуги")
        return
    data = await state.get_data()
    try:
        if AddService.service_for_change:
            await orm_update_service_by_id(session, AddService.service_for_change.id, data)
        else:
            await orm_add_service(session, data)
        await message.answer("Услуга добавлена/изменена", reply_markup=ADMIN_KB)
        await state.clear()

    except Exception as e:
        await message.answer(
            f"Ошибка: \n{str(e)}\nОбратись к Владу, он опять денег хочет",
            reply_markup=ADMIN_KB,
        )
        await state.clear()

    AddService.service_for_change = None

# Ловим все прочее некорректное поведение для этого состояния


@service_router_for_admin.message(AddService.image)
async def add_image2(message: types.Message, state: FSMContext):
    await message.answer("Отправьте фото услуги")
