from datetime import datetime

from sqlalchemy import DateTime, String, Text, Float, func, Numeric, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from database.Service import orm_get_service_prices_by_id
from database.models import Base, Order, OrderItem, Service


async def orm_add_to_order(
    session: AsyncSession,
    client_id: int,
    service_id: int,
    status_id: int,  # Обязательно передаем статус корзины
    plan_date: datetime = None,
    due_date: datetime = None
):
    # 1. Ищем существующий заказ (корзину)
    query = select(Order).where(
        Order.client_id == client_id,
        Order.status_id == status_id,
    ).options(selectinload(Order.items))

    result = await session.execute(query)
    order = result.scalar()

    # 2. Если заказа нет — создаем
    if not order:
        order = Order(
            client_id=client_id,
            status_id=status_id,
            plan_date=plan_date,
            due_date=due_date,
        )
        session.add(order)
        await session.flush()

    # 3. Ищем, есть ли уже такая услуга в этом заказе
    item_query = select(OrderItem).where(
        OrderItem.order_id == order.id,
        OrderItem.service_id == service_id
    )
    item_result = await session.execute(item_query)
    item = item_result.scalar()

    if item:
        item.quantity += 1
    else:
        # !!! ВАЖНО: Получаем актуальную цену услуги из БД
        service_query = select(Service.price).where(Service.id == service_id)
        service_result = await session.execute(service_query)
        current_price = service_result.scalar()

        if current_price is None:
            raise ValueError(f"Услуга с id {service_id} не найдена")

        session.add(OrderItem(
            order_id=order.id,
            service_id=service_id,
            quantity=1,
            price_at_runtime=current_price  # Фиксируем цену на момент заказа
        ))

    await session.commit()


async def orm_reduce_service_in_order(session: AsyncSession, client_id: int, service_id: int, status_id: int):
    # Находим нужный айтем через связь с заказом пользователя
    query = select(OrderItem).join(Order).where(
        Order.client_id == client_id,
        Order.status_id == status_id,
        OrderItem.service_id == service_id
    )

    result = await session.execute(query)
    item = result.scalar()

    if not item:
        return False

    if item.quantity > 1:
        item.quantity -= 1
        await session.commit()
        return True
    else:
        # Удаляем только одну услугу из заказа
        await session.delete(item)
        await session.commit()
        return False


async def orm_get_user_orders(session: AsyncSession, client_id: int):
    query = select(Order).where(Order.client_id == client_id).options(
        selectinload(Order.items).joinedload(
            OrderItem.service),  # Грузим айтемы + инфо об услуге
        joinedload(Order.status)  # Грузим название статуса
    )
    result = await session.execute(query)
    return result.scalars().all()


async def orm_update_order_details(
    session: AsyncSession,
    order_id: int,
    status_id: int = None,
    plan_date: datetime = None,
    due_date: datetime = None
):
    update_data = {}
    if status_id is not None:
        update_data["status_id"] = status_id
    if plan_date is not None:
        update_data["plan_date"] = plan_date
    if due_date is not None:
        update_data["due_date"] = due_date

    if not update_data:
        return  # Нечего обновлять

    query = (
        update(Order)
        .where(Order.id == order_id)
        .values(**update_data)
    )

    await session.execute(query)
    await session.commit()


async def orm_delete_from_order(session: AsyncSession, client_id: int, service_id: int, status_id: int = 1):
    query = (
        select(OrderItem)
        .join(Order)
        .where(
            Order.client_id == client_id,
            Order.status_id == status_id,
            OrderItem.service_id == service_id
        )
    )

    result = await session.execute(query)
    item = result.scalar()

    if not item:
        return False

    if item.quantity > 1:
        item.quantity -= 1
    else:
        await session.delete(item)

    await session.commit()
    return True


async def orm_clear_order(session: AsyncSession, client_id: int, status_id: int = 1):
    """Полная очистка корзины (удаление всего заказа)"""
    query = select(Order).where(Order.client_id ==
                                client_id, Order.status_id == status_id)
    result = await session.execute(query)
    order = result.scalar()

    if order:
        await session.delete(order)
        await session.commit()
