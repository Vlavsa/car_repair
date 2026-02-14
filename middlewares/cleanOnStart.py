from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest

class CleanOnStartMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Проверяем, начинается ли callback_data со "start"
        if event.data and event.data.startswith("admin"):
            try:
                # Удаляем сообщение с кнопками
                await event.message.delete()
                
                # Если нужно удалить и команду пользователя (предыдущее)
                await event.bot.delete_message(
                    chat_id=event.message.chat.id,
                    message_id=event.message.message_id - 1
                )
            except TelegramBadRequest:
                pass # Сообщение не найдено или слишком старое

        return await handler(event, data)
    
# class CleanChatMiddleware(BaseMiddleware):
#     async def __call__(self, handler, event: CallbackQuery, data):
#         # 1. Удаляем сообщение с кнопкой
#         try:
#             await event.message.delete()
            
#             # 2. Опционально: пробуем удалить сообщение пользователя, 
#             # которое вызвало это меню (обычно message_id - 1)
#             # Внимание: работает не всегда корректно в группах
#             await event.bot.delete_message(
#                 chat_id=event.message.chat.id, 
#                 message_id=event.message.message_id - 1
#             )
#         except TelegramBadRequest:
#             pass  # Если сообщение уже удалено или слишком старое

#         return await handler(event, data)
    
class CleanOnStartMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: CallbackQuery, data):
        # Список колбэков, которые должны ПРОСТО ОБНОВИТЬ текст (edit_text)
        # Для них удаление ВЫКЛЮЧЕНО
        keep_alive_callbacks = ["settings","orders","categories_list" , "admin_panel", "back_to_menu", "categories"]

        # Если колбэка нет в списке "сохраняемых" — удаляем сообщение
        if event.data not in keep_alive_callbacks:
            try:
                await event.message.delete()
            except TelegramBadRequest as e:
                print(e)

        return await handler(event, data)