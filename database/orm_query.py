from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from database.models import Service


async def orm_add_service(session: AsyncSession, data: dict):
    obj = Service(
        name=data["name"],
        description=data["description"],
        price=float(data["price"].replace(",", ".")),
        image=data["image"],
    )
    session.add(obj)
    await session.commit()


async def orm_get_services(session: AsyncSession):
    query = select(Service)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_service(session: AsyncSession, service_id:int):
    query = select(Service).where(Service.id == service_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_update_service(session: AsyncSession, service_id: int, data):
    query = update(Service).where(Service.id == service_id).values(
        name=data["name"],
        description=data["description"],
        price=float(data["price"].replace(",", ".")),
        image=data["image"],
    )
    await session.execute(query)
    await session.commit()


async def orm_delete_service(session: AsyncSession, service_id: int):
    query = delete(Service).where(Service.id == service_id)
    await session.execute(query)
    await session.commit()