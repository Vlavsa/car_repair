from sqlalchemy import DateTime, String, Text, Float, func, Numeric, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from database.models import Base, Category, Service


async def orm_check_category_by_id(session: AsyncSession, id_category):
    query = select(Category).where(Category.id == id_category)
    category = (await session.execute(query)).scalar_one_or_none()
    return category



async def orm_add_category(session: AsyncSession, data: dict):
    obj = Category(
        name=data["name"],
    )
    session.add(obj)
    await session.commit()


async def orm_create_categories(session: AsyncSession, categories: list):
    query = select(Category)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([Category(name=name) for name in categories])
    await session.commit()


async def orm_get_categories(session: AsyncSession):
    query = select(Category)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_category(session: AsyncSession, category_id: int):
    query = select(Category).where(Category.id == category_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_get_categories_inner_join_services(session: AsyncSession):
    query = select(Category).join(Category.services)
    result = await session.execute(query)
    return result.scalars().unique().all()


async def orm_get_categories_with_count_services(session: AsyncSession):
    query = (
        select(Category, func.count(Service.id).label('products_count'))
        .outerjoin(Service, Category.id == Service.category_id)
        .group_by(Category.id, Category.name)
    )
    result = await session.execute(query)
    # Убираем .scalars(), используем просто .all()
    return result.all() 


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
