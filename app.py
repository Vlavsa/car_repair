import os
import asyncio
import logging
import aiohttp

from db.db import create_tables

from aiogram.filters import CommandStart
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALOWED_UPDATES = ['message', 'edited_message']


# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')



from commands.bot_cmd_list import private as private_user_cmd
from handlers.user_private import user_router
from handlers.user_group import user_group_router
from handlers.user_admin import admin_router

# Обьект бота
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2))
bot.my_admins_list = []

dp = Dispatcher()

dp.include_router(user_router)
dp.include_router(user_group_router)
dp.include_router(admin_router)


async def main():

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())
    await bot.set_my_commands(commands=private_user_cmd, scope=types.BotCommandScopeAllPrivateChats())
    # await create_tables()
    await dp.start_polling(bot, allowed_updates=ALOWED_UPDATES)


if __name__ == "__main__":
    asyncio.run(main())
