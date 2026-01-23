import aiosqlite

table_name = 'Clients'

async def create_clients():
    async with aiosqlite.connect(DB_NAME) as db:

# Добавил свою модельку статусов заказов
# Может не заработать, т.к. скрипт написан под YQL
        await db.execute(f'''
CREATE TABLE IF NOT EXISTS OrderStatuses (
id uint64 NOT NULL,
code Utf8 NOT NULL,
name Utf8 NOT NULL,
PRIMARY KEY (id));''')
        await db.commit()
