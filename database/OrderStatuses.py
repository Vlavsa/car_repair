from sqlalchemy import DateTime, String, Text, Float, func, Numeric, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from database.models import OrderStatuses

async def orm_create_order_statuses(session: AsyncSession, name: str):
    ...

# Добавил свою модельку статусов заказов
# # Может не заработать, т.к. скрипт написан под YQL
#         await db.execute(f'''
# CREATE TABLE IF NOT EXISTS OrderStatuses (
# id uint64 NOT NULL,
# code Utf8 NOT NULL,
# name Utf8 NOT NULL,
# PRIMARY KEY (id));''')
#         await db.commit()
