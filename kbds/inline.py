from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton


def get_callback_btns(
        *,
        btns: dict[str, str],
        sizes: tuple[int] = (2,),
):
    builder = InlineKeyboardBuilder()

    for text, data in btns.items():
        builder.add(InlineKeyboardButton(text=text, callback_data=data))

    
    return builder.adjust(*sizes).as_markup() # При нажатии вернет callback_data



def get_url_btns(
    *, 
    btns: dict[str, str], 
    sizes: tuple[int] = (2,)
):
    builder = InlineKeyboardBuilder()

    for text, url in btns.items():
        builder.add(InlineKeyboardButton(text=text, url=url))

    builder.adjust(*sizes)
    return builder.as_markup()# При нажатии вернет url


def get_inlineMix_btns(
    *, 
    btns: dict[str, str], 
    sizes: tuple[int] = (2,)
):
    builder = InlineKeyboardBuilder()

    for text, value in btns.items():
        if '://' in value:
            builder.add(InlineKeyboardButton(text=text, url=value))
        else:
            builder.add(InlineKeyboardButton(text=text, callback_data=value))

    builder.adjust(*sizes)
    return builder.as_markup()# При нажатии вернет url