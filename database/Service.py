from sqlalchemy import DateTime, String, Text, Float, func, Numeric, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from database.models import Base, Service


async def orm_add_service(session: AsyncSession, data: dict):
    obj = Service(
        name=data["name"],
        description=data["description"],
        price=float(data["price"].replace(",", ".")),
        image=data["image"],
        category_id=int(data['category'])
    )
    session.add(obj)
    await session.commit()


async def orm_get_services_by_category_id(session: AsyncSession, category_id):
    query = select(Service).where(Service.category_id == int(category_id))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_service_by_id(session: AsyncSession, service_id: int):
    query = select(Service).where(Service.id == service_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_update_service_by_id(session: AsyncSession, service_id: int, data):
    query = update(Service).where(Service.id == service_id).values(
        name=data["name"],
        description=data["description"],
        price=float(data["price"].replace(",", ".")),
        image=data["image"],
        category_id=int(data['category']))
    await session.execute(query)
    await session.commit()


async def orm_delete_service_by_id(session: AsyncSession, service_id: int):
    query = delete(Service).where(Service.id == service_id)
    await session.execute(query)
    await session.commit()
