from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

start_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Магазин"),
            KeyboardButton(text="Сервис"),
   
         ]
         ,[
            KeyboardButton(text="Оплата"),
            KeyboardButton(text="Доставка"),
            KeyboardButton(text="О нас!"),
         ]
    ],
    resize_keyboard=True, 
    input_field_placeholder="Что вас интересует?"
)