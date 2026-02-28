from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, BigInteger, Integer, String, Text, DateTime, Numeric, Date, Time, Boolean, UniqueConstraint, func, select, update, delete
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, date, time

from sqlalchemy import DateTime, String, Text, Float, func, Numeric, ForeignKey, BigInteger, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now())


class Client(Base):
    __tablename__ = 'clients'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_client: Mapped[int] = mapped_column(BigInteger, unique=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    username: Mapped[str] = mapped_column(String(150), nullable=False)
    phone_number: Mapped[str] = mapped_column(
        String(20), unique=True, index=True)

    orders: Mapped[List["Order"]] = relationship(back_populates="client")


class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)

    services: Mapped[List["Service"]] = relationship(back_populates="category")


class Service(Base):
    __tablename__ = 'services'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    image: Mapped[Optional[str]] = mapped_column(String(150))

    category_id: Mapped[int] = mapped_column(ForeignKey(
        'categories.id', ondelete='CASCADE'), nullable=False)
    category: Mapped["Category"] = relationship(back_populates="services")

    order_items: Mapped[List["OrderItem"]] = relationship(
        back_populates="service")


class Order(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    plan_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    client_id: Mapped[int] = mapped_column(ForeignKey('clients.id_client'))
    status_id: Mapped[int] = mapped_column(ForeignKey('statusorders.id'))

    client: Mapped["Client"] = relationship(back_populates="orders")
    status: Mapped["OrderStatuses"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin"
    )


class OrderItem(Base):
    __tablename__ = 'order_items'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey('orders.id', ondelete='CASCADE'))
    service_id: Mapped[int] = mapped_column(ForeignKey('services.id'))

    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price_at_runtime: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    order: Mapped["Order"] = relationship(back_populates="items")
    service: Mapped["Service"] = relationship(back_populates="order_items")


class OrderStatuses(Base):
    __tablename__ = 'statusorders'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)
    orders: Mapped[List["Order"]] = relationship(back_populates="status")


class Banner(Base):
    __tablename__ = 'banners'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(15), unique=True)
    image: Mapped[Optional[str]] = mapped_column(String(150))
    description: Mapped[Optional[str]] = mapped_column(Text)


class TimeSlot(Base):
    __tablename__ = 'time_slots'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    time_start: Mapped[time] = mapped_column(Time, nullable=False)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False)

    # Связь с заказом, если слот уже занят
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey('orders.id'))


    __table_args__ = (
        UniqueConstraint('date', 'time_start', name='uq_date_time_slots'),
    )