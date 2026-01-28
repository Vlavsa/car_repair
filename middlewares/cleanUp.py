from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

class CleanUpMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем доступ к FSM состоянию
        state: FSMContext = data.get("state")
        
        if state:
            state_data = await state.get_data()
            last_msg_id = state_data.get("last_msg_id")
            
            # 1. Пытаемся удалить предыдущее сообщение бота
            if last_msg_id:
                try:
                    await event.bot.delete_message(
                        chat_id=event.chat.id, 
                        message_id=last_msg_id
                    )
                except TelegramBadRequest:
                    # Сообщение уже удалено или слишком старое
                    pass

        # 2. Выполняем сам хендлер
        result = await handler(event, data)
        
        # 3. Если хендлер отправил новое сообщение (мы его сохраним позже в хендлере)
        # Или можно сохранять его автоматически здесь, если хендлер возвращает Message
        if isinstance(result, Message):
            await state.update_data(last_msg_id=result.message_id)
            
        return result