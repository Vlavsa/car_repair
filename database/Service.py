from sqlalchemy import DateTime, String, Text, Float, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from database.models import Base


class Services(Base):
    __tablename__ = 'service'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float(asdecimal=True), nullable=False)
    image: Mapped[str] = mapped_column(String(150))


async def orm_add_service(session: AsyncSession, data: dict):
    obj = Services(
        name=data["name"],
        description=data["description"],
        price=float(data["price"].replace(",", ".")),
        image=data["image"],
    )
    session.add(obj)
    await session.commit()


async def orm_get_services(session: AsyncSession):
    query = select(Services)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_service(session: AsyncSession, service_id: int):
    query = select(Services).where(Services.id == service_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_update_service(session: AsyncSession, service_id: int, data):
    query = update(Services).where(Services.id == service_id).values(
        name=data["name"],
        description=data["description"],
        price=float(data["price"].replace(",", ".")),
        image=data["image"],
    )
    await session.execute(query)
    await session.commit()


async def orm_delete_service(session: AsyncSession, service_id: int):
    query = delete(Services).where(Services.id == service_id)
    await session.execute(query)
    await session.commit()
