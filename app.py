import os
import asyncio
import logging
import aiohttp

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from middlewares.db import DataBaseSession

from database.engine import create_db, drop_db, session_maker

from commands.bot_cmd_list import private as private_user_cmd

from handlers.user_private import user_router
from handlers.user_group import user_group_router
from handlers.user_admin import admin_router

API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALOWED_UPDATES = ['message', 'edited_message', 'callback_query']


# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# Обьект бота
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(
    parse_mode=ParseMode.HTML))
bot.my_admins_list = []

dp = Dispatcher() 

dp.include_router(user_router)
dp.include_router(user_group_router)
dp.include_router(admin_router)


async def on_startup():
    run_param = False
    if run_param:
        await drop_db()

    await create_db()

async def on_shutdown():
    print('Бот лёг')

async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)


    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    await bot.delete_webhook(drop_pending_updates=True)
    # await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())
    await bot.set_my_commands(commands=private_user_cmd, scope=types.BotCommandScopeAllPrivateChats())
    # await create_tables()

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        # Корректное закрытие соединений (исправляет ошибку Unclosed connector)
        await bot.session.close()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
