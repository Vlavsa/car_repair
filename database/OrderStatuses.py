from sqlalchemy import DateTime, String, Text, Float, func, Numeric, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from database.models import OrderStatuses

async def orm_create_initial_data(session: AsyncSession):
    # Проверяем, есть ли уже статусы
    query = select(OrderStatuses).where(OrderStatuses.id == 1)
    result = await session.execute(query)
    
    if not result.scalar():
        # Добавляем базовые статусы
        session.add_all([
            OrderStatuses(id=1, name='В корзине'),
            OrderStatuses(id=2, name='Оформлен'),
            OrderStatuses(id=3, name='В работе'),
            OrderStatuses(id=4, name='Ожидание запчастей'),
            OrderStatuses(id=5, name='Готов к выдаче'),
            OrderStatuses(id=6, name='Выполнено'),
            OrderStatuses(id=7, name='Отмена'),
        ])
        await session.commit()

