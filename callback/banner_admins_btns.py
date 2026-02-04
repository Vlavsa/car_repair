from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton


class BannerClick(CallbackData, prefix="ban"):
    action: str     # "view", "delete", "prev", "next"
    banner_id: int = 0
    banner_name: str = ''
    page: int = 0
