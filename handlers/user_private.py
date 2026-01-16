from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command, or_f


from filters.filters_type import ChatTypeFilter
from aiogram.utils.formatting import as_list, as_marked_section, Bold #Italic, as_numbered_list и тд 


from kbds import replay
from kbds.replay import kb, get_keyboard

user_router = Router()
user_router.message.filter(ChatTypeFilter(['private']))
user_router.edited_message.filter(ChatTypeFilter(['private']))


@user_router.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer(
        "Привет, я виртуальный помощник",
        reply_markup=get_keyboard(
            "Магазин"
            "Сервис"
            "Варианты оплаты",
            "Варианты доставки",
            "О нас!",
            placeholder="Что вас интересует?",
            sizes=(2, 2, 1)
        ),
    )


@user_router.message(or_f(Command('shop'), (F.text.lower().contains('ката')), (F.text.lower().contains('магазин'))))
async def magic_filters(message: types.Message):
    await message.answer('Категории: ')


@user_router.message((F.text.lower().contains('работа')) | (F.text.lower().contains('сервис')) | (F.text.lower().contains('услуги')))
@user_router.message(Command('service'))
async def magic_filters(message: types.Message):
    await message.answer('Сервис: ')


@user_router.message(F.text.lower().contains('оплат') | F.text.lower().contains('cash'))
@user_router.message(Command('payment'))
async def magic_filters(message: types.Message):
    await message.answer('Оплата: ')

@user_router.message((F.text.lower().contains('about')) | (F.text.lower().contains('инф')) | (F.text.lower().contains('адрес')) | (F.text.lower().contains('о нас')))
@user_router.message(Command('about'))
async def magic_filters(message: types.Message):
    await message.answer('О нас!')


@user_router.message(F.text.lower().contains('доставк'))
@user_router.message(Command('shipping'))
async def magic_filters(message: types.Message):
    text = as_list(
        as_marked_section(
            Bold("Варианты доставки/заказа:"),
            "Самовынос (сейчас прибегу заберу)",
            marker='✅ '
        ),
        as_marked_section(
            Bold("Нельзя:"),
            "Курьер",
            "Почта",
            "Голуби",
            marker='❌ '
        ),
        sep='\n-------------\n'
    )
    await message.answer(text.as_markdown())


@user_router.message(F.contact)
async def get_contact(message: types.Message):
    await message.answer(f"Номер получен")
    await message.answer(str(message.contact))


@user_router.message(F.location)
async def get_location(message: types.Message):
    await message.answer(f"Геолокация получена")
    await message.answer(str(message.location))