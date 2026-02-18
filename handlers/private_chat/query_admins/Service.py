from decimal import Decimal
from aiogram import F, Router, types

from aiogram.types import InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder


from database.Paginator import Paginator, pages
from kbds.inline.categories_admin import CategoryClick
from kbds.inline.inline import get_callback_btns, button_service_admin, button_categories_admin
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
    orm_check_category_by_id,
    orm_get_categories,
    orm_get_categories_inner_join_services
)


service_router_for_admin = Router()
service_router_for_admin.message.filter(ChatTypeFilter(["private"]), IsAdmin())


######################### FSM для дабавления/изменения товаров админом ###################
class ClickService(CallbackData, prefix="service_"):
    pref: str  # delete, update, confirm_delete
    category_id: int | None = None
    service_id: int | None = None
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
        kb.row(types.InlineKeyboardButton(text='➕ Добавить услугу',
               callback_data=ClickService(pref="add", category_id=category_id).pack()))
        kb.row(types.InlineKeyboardButton(text='🔙 Назад',
               callback_data=MenuCallBackAdmin(level=level-1, menu_name='category').pack()))
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
    # Добавляем кнопку возврата к категориям
    kb.row(types.InlineKeyboardButton(text='➕ Добавить услугу',
               callback_data=ClickService(pref="add", category_id=category_id).pack()))
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

    # ОБЯЗАТЕЛЬНО передаем category_id, чтобы не терять контекст
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

    # Ряд пагинации
    nav_row = []
    for text, action in pagination_btns.items():
        # Вычисляем целевую страницу
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

# @service_router_for_admin.callback_query(CategoryClick.filter(F.action == "category_"))
# async def starring_at_service(callback: types.CallbackQuery, session: AsyncSession, callback_data: CategoryClick, state: FSMContext):
#     category_id = callback_data.category_id
#     query = await orm_get_services_by_category_id(session=session, category_id=int(category_id))

#     await state.clear()
#     await state.update_data(category=category_id)

#     if not query or len(query) < 1:
#         await callback.answer()
#         return await callback.message.answer('Список пуст....', reply_markup=button_service_admin)

#     await callback.message.delete()
#     await callback.answer()

#     for service in query:
#         await callback.message.answer_photo(
#             service.image,
#             caption=f"<strong>{service.name}\
#                     </strong>\n{service.description}\nСтоимость: {round(service.price, 2)}",
#             reply_markup=get_callback_btns(
#                 btns={
#                     "Удалить": f"delete_{service.id}",
#                     "Изменить": f"change_{service.id}",
#                 },
#                 sizes=(2,)
#             ),
#         )
#     await callback.answer()
#     await callback.message.answer("ОК, вот список товаров ⏫", reply_markup=button_service_admin)


# @service_router_for_admin.callback_query(F.data.startswith("delete_"))
# async def delete_service_callback(callback: types.CallbackQuery, session: AsyncSession):
#     product_id = callback.data.split("_")[-1]
#     await orm_delete_service_by_id(session, int(product_id))

#     await callback.answer("Услуга удалена")
#     await callback.message.answer("Услуга удалена!")
#     return await callback.message.delete()


# # Становимся в состояние ожидания ввода name


# @service_router_for_admin.callback_query(StateFilter(None), F.data.startswith("change_"))
# async def change_service_callback(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
#     service_id = int(callback.data.split("_")[-1])
#     service_for_change = await orm_get_service_by_id(session, service_id)

#     # Сохраняем данные услуги в state, чтобы они были доступны во всех хендлерах
#     await state.update_data(
#         service_id=service_for_change.id,
#         old_name=service_for_change.name,
#         old_description=service_for_change.description,
#         old_category=service_for_change.category,
#         old_price=service_for_change.price,
#         old_image=service_for_change.image
#     )

#     await callback.answer()
#     await callback.message.answer(
#         f"Меняем: {service_for_change.name}\nВведите новое название или '.'",
#         reply_markup=types.ReplyKeyboardRemove()
#     )
#     await state.set_state(AddService.name)


# # Становимся в состояние ожидания ввода name
# @service_router_for_admin.callback_query(F.data == "add_service")
# async def add_service(callback: types.CallbackQuery, state: FSMContext):
#     await callback.answer()
#     await callback.message.answer(
#         "Введите название услуги", reply_markup=types.ReplyKeyboardRemove()
#     )
#     await state.set_state(AddService.name)


# @service_router_for_admin.message(AddService.name)
# async def add_name(message: types.Message, state: FSMContext):
#     if len(message.text) > 150:
#         return await message.answer("Название слишком длинное (макс. 150 симв.)")

#     data = await state.get_data()
#     service_id = data.get("service_id")

#     if message.text == "." and service_id:
#         await state.update_data(name=data.get("old_name"))
#     else:
#         if not (5 <= len(message.text) <= 150):
#             return await message.answer("Описание должно быть от 5 до 150 символов.")
#         await state.update_data(name=message.text)

#     if service_id:
#         await message.answer(f"Старое описание: {data.get('old_description')}\nВведите новое или '.'")
#     else:
#         await message.answer("Введите описание услуги:")

#     await state.set_state(AddService.description)

# # Ловим description


# @service_router_for_admin.message(AddService.description)
# async def add_description(message: types.Message, state: FSMContext):
#     data = await state.get_data()
#     service_id = data.get("service_id")

#     if message.text == "." and service_id:
#         await state.update_data(description=data.get("old_description"))
#     else:
#         # Исправленная проверка длины
#         if not (5 <= len(message.text) <= 150):
#             return await message.answer("Описание должно быть от 5 до 150 символов.")
#         await state.update_data(description=message.text)

#     if service_id:
#         await message.answer(f"Старая цена: {data.get('old_price')}\nВведите новую или '.'")
#     else:
#         await message.answer("Введите цену услуги:")

#     await state.set_state(AddService.price)


# @service_router_for_admin.message(AddService.price, or_f(F.text, F.text == "."))
# async def add_price(message: types.Message, state: FSMContext, session: AsyncSession):
#     data = await state.get_data()
#     service_id = data.get("service_id")
#     category = data.get('category')
#     print('_____________________________________________________________')
#     print(category)
#     # 1. Если ввели точку при редактировании
#     if message.text == "." and service_id:
#         old_price = data.get("old_price")

#         # Безопасно сохраняем как число
#         await state.update_data(price=old_price)
#         await message.answer("Цена оставлена прежней. Будете менять фото? Отправьте новое или '.'")
#         await state.set_state(AddService.image)
#         return

#     # 2. Если это ввод новой цены (или создание новой услуги)
#     price_text = message.text.replace(" ", "").replace(",", ".")

#     try:

#         price_val = Decimal(price_text)
#         if -1 >  price_val > 999999:
#             return await message.answer("Число не может быть больше 999 999 или меньше 0")


#         await state.update_data(price=price_val)

#         if service_id:
#             await message.answer("Цена обновлена. Выберите категорию или '.'")
#             await state.set_state(AddService.category)
#         else:
#             if category:
#                 await message.answer("Теперь загрузите фотографию")
#                 await state.set_state(AddService.image)
#             else:
#                 categories = await orm_get_categories(session=session)
#                 categories_data = {cat.name: f"cat_{cat.id}" for cat in categories}
#                 await message.answer("Теперь выберите категорию", reply_markup=get_callback_btns(btns=categories_data, sizes=(2,)))
#                 await state.set_state(AddService.category)

#     except Exception as e:
#         await message.answer(
#             f"Введите корректное число (по типу 500.00 или 5000,00)")
#         print(e)

# @service_router_for_admin.callback_query(AddService.category, or_f(F.data.startswith('cat_'), F.text == "."))
# async def add_categories_for_service(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
#     if callback.data == ".":

#         data = await state.get_data()
#         id_category = data.get("old_category")
#         await state.update_data(category=id_category)
#         await callback.message.answer("Теперь добавить фотографию")
#         await callback.answer()
#         await state.set_state(AddService.image)


#     id_category = int(callback.data.split('_')[-1])
#     category =  await orm_check_category_by_id(session=session, id_category=id_category)

#     if not category:
#             categories = await orm_get_categories(session=session)
#             categories_data = {cat.name: f"cat_{cat.id}" for cat in categories}
#             await callback.message.answer("Выберите категорию из доступных", reply_markup=get_callback_btns(btns=categories_data, sizes=(2,)))
#             await callback.answer()
#             return

#     await state.update_data(category=id_category)
#     await callback.message.answer("Теперь добавить фотографию")
#     await callback.answer()
#     await state.set_state(AddService.image)


# @service_router_for_admin.message(AddService.image, or_f(F.photo, F.text == "."))
# async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):
#     data = await state.get_data()
#     print(f"DEBUG: Функция дошла до конца! Входящие данные: {data}")
#     # Проверяем, редактируем ли мы или создаем
#     service_id = data.get("service_id")

#     # 1. Определяем, какое изображение использовать
#     if message.text == ".":
#         if service_id:
#             # Если точка при редактировании — берем старое фото
#             image_to_save = data.get("old_image")
#         else:
#             return await message.answer("При добавлении новой услуги нельзя ставить точку. Отправьте фото.")
#     elif message.photo:
#         # Если прислали новое фото — берем его
#         image_to_save = message.photo[-1].file_id
#     else:
#         return await message.answer("Пожалуйста, отправьте фото услуги или '.' для сохранения старого.")

#     # Обновляем data финальным фото
#     await state.update_data(image=image_to_save)

#     # 2. Получаем все накопленные данные из FSM
#     final_data = await state.get_data()
#     print(final_data)
#     try:
#         if service_id:
#             # Если есть ID — вызываем UPDATE
#             await orm_update_service_by_id(session, service_id, final_data)
#             await message.answer("Услуга успешно обновлена!", reply_markup=button_service_admin)
#         else:
#             # Если ID нет — вызываем INSERT
#             await orm_add_service(session, final_data)
#             await message.answer("Услуга успешно добавлена!", reply_markup=button_service_admin)

#         # 3. Обязательно очищаем состояние
#         await state.clear()

#     except Exception as e:
#         print(e)
#         await message.answer(
#             f"Отправьте корректно изображиние..."
#         )
