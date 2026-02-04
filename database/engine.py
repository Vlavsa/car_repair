import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.models import Base
from database.Category import orm_create_categories
from database.Banner import orm_add_banner_description

from commands.texts_for_db import description_for_info_pages, categories


#
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')


DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_async_engine(DATABASE_URL, echo=True)

session_maker = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession)


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        await orm_create_categories(session, categories)
        await orm_add_banner_description(session, description_for_info_pages) ## Добавляем страницы баннеров


# async def drop_db():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.drop_all)


from sqlalchemy import text

async def drop_db():
    async with engine.begin() as conn:
        # Получаем список всех таблиц в схеме public
        result = await conn.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        ))
        tables = result.scalars().all()
        
        if tables:
            # Склеиваем имена таблиц через запятую и добавляем CASCADE
            tables_str = ", ".join(tables)
            await conn.execute(text(f"DROP TABLE IF EXISTS {tables_str} CASCADE"))
            print(f"База очищена. Удалены таблицы: {tables_str}")