import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.models import Base


DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

DB_LITE = os.getenv('DB_LITE')


engine = create_async_engine(DB_LITE, echo=True)

session_maker = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        



