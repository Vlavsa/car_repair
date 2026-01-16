from aiogram import F, Router, types
from aiogram.filters import Command

from filters.filters_type import ChatTypeFilter, IsAdmin
from kbds.replay import get_keyboard


admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())


ADMIN_KB = get_keyboard(
    "Добавить работу",
    "Изменить работу",
    "Удалить работу",
    "Я так, просто посмотреть зашел",
    placeholder="Выберите действие",
    sizes=(2, 1, 1),
)


@admin_router.message(Command("admin"))
async def add_service(message: types.Message):
    await message.answer("Что хотите сделать?", reply_markup=ADMIN_KB)


@admin_router.message(F.text == "Я так, просто посмотреть зашел")
async def starring_at_service(message: types.Message):
    await message.answer("ОК, вот список работ")


@admin_router.message(F.text == "Изменить работу")
async def change_service(message: types.Message):
    await message.answer("ОК, вот список работ")


@admin_router.message(F.text == "Удалить работу")
async def delete_service(message: types.Message):
    await message.answer("Выберите работу(ы) для удаления")


#Код ниже для машины состояний (FSM)

@admin_router.message(F.text == "Добавить работу")
async def add_service(message: types.Message):
    await message.answer(
        "Введите название работы", reply_markup=types.ReplyKeyboardRemove()
    )


@admin_router.message(Command("отмена"))
@admin_router.message(F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message) -> None:
    await message.answer("Действия отменены", reply_markup=ADMIN_KB)


@admin_router.message(Command("назад"))
@admin_router.message(F.text.casefold() == "назад")
async def cancel_handler(message: types.Message) -> None:
    await message.answer(f"ок, вы вернулись к прошлому шагу")


@admin_router.message(F.text)
async def add_name(message: types.Message):
    await message.answer("Введите описание работы")


@admin_router.message(F.text)
async def add_description(message: types.Message):
    await message.answer("Введите стоимость работы")


@admin_router.message(F.text)
async def add_price(message: types.Message):
    await message.answer("Загрузите изображение работы")


@admin_router.message(F.photo)
async def add_image(message: types.Message):
    await message.answer("Работа добавлена", reply_markup=ADMIN_KB)