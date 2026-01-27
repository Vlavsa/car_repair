from sqlalchemy import DateTime, String, Text, Float, func, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from database.models import Base


class Category(Base):
    __tablename__ = ' category'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)


async def orm_add_category(session: AsyncSession, data: dict):
    obj = Category(
        name=data["name"],
    )
    session.add(obj)
    await session.commit()


async def orm_get_categories(session: AsyncSession):
    query = select(Category)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_category(session: AsyncSession, category_id: int):
    query = select(Category).where(Category.id == category_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_update_category(session: AsyncSession, category_id: int, data):
    query = update(Category).where(Category.id == category_id).values(
        name=data["name"],
    )
    await session.execute(query)
    await session.commit()


async def orm_delete_category(session: AsyncSession, category_id: int):
    query = delete(Category).where(Category.id == category_id)
    await session.execute(query)
    await session.commit()
