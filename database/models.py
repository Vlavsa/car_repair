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


class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)


class Service(Base):
    __tablename__ = 'services'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    image: Mapped[str] = mapped_column(String(150))

    category_id: Mapped[int] = mapped_column(ForeignKey(
        'categories.id', ondelete='CASCADE'), nullable=False)

    category: Mapped['Category'] = relationship(backref='services')


class Banner(Base):
    __tablename__ = 'banners'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(15), unique=True)
    image: Mapped[str] = mapped_column(String(150), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)


class Order(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    client_id: Mapped[int] = mapped_column(ForeignKey(
        'clients.id_client', ondelete='CASCADE'), nullable=False)
    service_id: Mapped[int] = mapped_column(ForeignKey(
        'services.id', ondelete='CASCADE'), nullable=False)
    
    quantity: Mapped[int]

    client: Mapped['Client'] = relationship(backref='orders')
    service: Mapped['Service'] = relationship(backref='orders')
