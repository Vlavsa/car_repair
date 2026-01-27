from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext


from sqlalchemy.ext.asyncio import AsyncSession

from .Service import service_router_for_admin

from filters.chat_type import ChatTypeFilter, IsAdmin

from kbds.reply import get_keyboard, ADMIN_KB


admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())


admin_router.include_routers(
    service_router_for_admin,
)


@admin_router.message(Command("admin"))
async def admin_features(message: types.Message):
    await message.answer("Что хотите сделать?", reply_markup=ADMIN_KB)
