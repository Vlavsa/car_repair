from sqlalchemy import DateTime, String, Text, Float, func, Numeric, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from database.models import Banner


async def orm_add_banner_description(session: AsyncSession, data: dict):
    # Добавляем новый или изменяем существующий по именам
    # пунктов меню: main, about, order, shipping, payment, catalog
    query = select(Banner)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([Banner(name=name, description=description)
                    for name, description in data.items()])
    await session.commit()


async def orm_change_banner_image(session: AsyncSession, name: str, image: str):
    query = update(Banner).where(Banner.name == name).values(image=image)
    await session.execute(query)
    await session.commit()


async def orm_update_banner_image(session: AsyncSession, banner_id: int, image):
    query = update(Banner).where(Banner.id == banner_id).values(
        image=image
    )
    await session.execute(query)
    await session.commit()


async def orm_get_banner_by_id(session: AsyncSession, banner_id: int):
    query = select(Banner).where(Banner.id == banner_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_get_banner(session: AsyncSession, page: str):
    query = select(Banner).where(Banner.name == page)
    result = await session.execute(query)
    return result.scalar()


async def orm_get_banners(session: AsyncSession):
    query = select(Banner)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_info_pages(session: AsyncSession):
    query = select(Banner)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_update_banner_by_id(session: AsyncSession, banner_id: int, data):
    query = update(Banner).where(Banner.id == banner_id).values(
        description=data["description"],
        image=data["image"]
    )
    await session.execute(query)
    await session.commit()
