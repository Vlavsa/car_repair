from aiogram.types import BotCommand

# Список команд в меню телеграм бота

private = [
    BotCommand(command='shop', description='Магазин'),
    BotCommand(command='service', description='Сервис'),
    BotCommand(command='payment', description='Варианты оплаты'),
    BotCommand(command='shipping', description='Варианты доставки'),
    BotCommand(command='about', description='О нас\\!'),
]