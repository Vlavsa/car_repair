from sqlalchemy import DateTime, String, Text, Float, func, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from database.models import Base, Client


async def orm_check_client(session: AsyncSession, client_id):
    query = select(Client).where(Client.id_client == client_id)
    user = (await session.execute(query)).scalar_one_or_none()
    return user

async def orm_add_client(session: AsyncSession, id_client: int, name: str, username: str, phone_number):
    # Проверяем, есть ли уже такой клиент по его telegram id (id_client)
    query = select(Client).where(Client.id_client == id_client)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        session.add(
            Client(
                id_client=id_client,
                name=name,
                username=username,
                phone_number=phone_number
            )
        )
        await session.commit()



async def orm_get_client(session: AsyncSession, client_id: int):
    query = select(Client).where(Client.id == client_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_get_clients(session: AsyncSession):
    query = select(Client)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_update_client_by_id(session: AsyncSession, client_id: int, data: dict):
    query = update(Client).where(Client.id == client_id).values(
        name=data["name"],
        username=data["username"],
        phone_number=data["phone_number"],
    )
    await session.execute(query)
    await session.commit()


async def orm_delete_client_by_id(session: AsyncSession, client_id: int):
    query = delete(Client).where(Client.id == client_id)
    await session.execute(query)
    await session.commit()
