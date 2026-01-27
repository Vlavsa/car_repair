from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command, or_f
from aiogram.fsm.state import StatesGroup, State

from sqlalchemy.ext.asyncio import AsyncSession


from database.orm_query import orm_get_services
from filters.chat_type import ChatTypeFilter
# Italic, as_numbered_list и тд
from aiogram.utils.formatting import as_list, as_marked_section, Bold


from kbds import reply
from kbds.inline import get_callback_btns
from kbds.reply import kb, get_keyboard

user_router = Router()
user_router.message.filter(ChatTypeFilter(['private']))
user_router.edited_message.filter(ChatTypeFilter(['private']))


@user_router.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer(
        "Привет, я виртуальный помощник",
        reply_markup=get_keyboard(
            # "Магазин"1
            "Сервис"
            "Варианты оплаты",
            "Варианты доставки",
            "О нас!",
            placeholder="Что вас интересует?",
            sizes=(2, 2)
        ),
    )


@user_router.message(or_f(Command('shop'), (F.text.lower().contains('ката')), (F.text.lower().contains('магазин'))))
async def magic_filters(message: types.Message):
    await message.answer('Категории: ')



@user_router.message((F.text.lower().contains('работа')) | (F.text.lower().contains('сервис')) | (F.text.lower().contains('услуги')))
@user_router.message(Command('service'))
async def menu_service(message: types.Message, session: AsyncSession):



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
