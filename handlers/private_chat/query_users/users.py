from aiogram import F, types, Router
from aiogram.filters import CommandStart

from sqlalchemy.ext.asyncio import AsyncSession


from filters.chat_types import ChatTypeFilter


from handlers.private_chat.query_users.menu_processing import get_menu_content

user_router = Router()
user_router.message.filter(ChatTypeFilter(["private"]))


@user_router.message(CommandStart())
async def start_cmd(message: types.Message, session: AsyncSession):
    media, reply_markup = await get_menu_content(session, level=0, menu_name="main")
    await message.answer_photo(media.media, caption=media.caption, reply_markup=reply_markup)
