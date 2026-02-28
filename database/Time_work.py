from datetime import datetime
from datetime import date, time, timedelta
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import DateTime, String, Text, Float, func, Numeric, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import TimeSlot

async def orm_generate_slots(session: AsyncSession, target_date: date, start_h: int = 8, end_h: int = 18):
    step = timedelta(hours=1)
    
    current_time = datetime.combine(target_date, time(start_h, 0))
    end_time = datetime.combine(target_date, time(end_h, 0))
    
    slots_to_add = []


    while current_time < end_time:
        slots_to_add.append({
            "date": target_date,
            "time_start": current_time.time(),
            "is_booked": False
        })
        current_time += step


    stmt = insert(TimeSlot).values(slots_to_add)
    
    stmt = stmt.on_conflict_do_nothing(
        index_elements=['date', 'time_start']
    )
    
    await session.execute(stmt)
    await session.commit()


async def orm_get_available_dates(session: AsyncSession):
    query = (
        select(TimeSlot.date)
        .where(TimeSlot.is_booked == False, TimeSlot.date >= date.today())
        .distinct()
        .order_by(TimeSlot.date)
    )
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_available_slots(session: AsyncSession, target_date: date):
    query = (
        select(TimeSlot)
        .where(TimeSlot.date == target_date, TimeSlot.is_booked == False)
        .order_by(TimeSlot.time_start)
    )
    result = await session.execute(query)
    return result.scalars().all()



async def orm_book_slot(session: AsyncSession, slot_id: int, order_id: int):
    query = (
        update(TimeSlot)
        .where(TimeSlot.id == slot_id)
        .values(is_booked=True, order_id=order_id)
    )
    await session.execute(query)
    await session.commit()


async def orm_delete_slots_on_date(session: AsyncSession, target_date: date):
    query = delete(TimeSlot).where(
        TimeSlot.date == target_date, 
        TimeSlot.is_booked == False
    )
    await session.execute(query)
    await session.commit()


async def get_last_configured_date(session: AsyncSession):
    query = select(func.max(TimeSlot.date))
    result = await session.execute(query)
    return result.scalar()


async def orm_delete_all_free_slots(session: AsyncSession):
    # Удаляем только те слоты, которые НЕ забронированы
    query = delete(TimeSlot).where(TimeSlot.is_booked == False)
    await session.execute(query)
    await session.commit()