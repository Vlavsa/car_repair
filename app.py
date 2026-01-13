import os
import asyncio
import logging

from db import create_tables

from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DB_NAMES = os.getenv('DB_NAMES')
print(API_TOKEN)
print(DB_NAMES)


# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Обьект бота
bot = Bot(API_TOKEN)


# async def main():

    # await create_table(DB_NAME)
#     await dp.start_polling(bot)


# if __name__ == "__main__":
#     asyncio.run(main())
