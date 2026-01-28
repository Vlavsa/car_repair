from sqlalchemy import DateTime, String, Text, Float, func, Numeric, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from database.models import Base, Order


async def orm_add_to_order(session: AsyncSession, client_id: int, service_id: int):
    query = select(Order).where(Order.client_id == client_id,
                               Order.service_id == service_id).options(joinedload(Order.product))
    cart = await session.execute(query)
    cart = cart.scalar()
    if cart:
        cart.quantity += 1
        await session.commit()
        return cart
    else:
        session.add(Order(client_id=client_id,
                    service_id=service_id, quantity=1))
        await session.commit()


async def orm_get_user_orders(session: AsyncSession, client_id):
    query = select(Order).filter(Order.client_id ==
                                client_id).options(joinedload(Order.service))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_delete_from_order(session: AsyncSession, client_id: int, service_id: int):
    query = delete(Order).where(Order.client_id == client_id,
                               Order.service_id == service_id)
    await session.execute(query)
    await session.commit()


async def orm_reduce_service_in_order(session: AsyncSession, client_id: int, service_id: int):
    query = select(Order).where(Order.client_id == client_id,
                               Order.service_id == service_id).options(joinedload(Order.service))
    cart = await session.execute(query)
    cart = cart.scalar()

    if not cart:
        return
    if cart.quantity > 1:
        cart.quantity -= 1
        await session.commit()
        return True
    else:
        await orm_delete_from_order(session, client_id, service_id)
        await session.commit()
        return False
