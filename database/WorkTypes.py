import aiosqlite

table_name = 'Clients'

async def create_clients():
    async with aiosqlite.connect(DB_NAME) as db:

# Добавил свою модельку видов работ
# Может не заработать, т.к. скрипт написан под YQL
        await db.execute(f'''
CREATE TABLE IF NOT EXISTS WorkTypes (
id uint64 NOT NULL,
code Utf8 NOT NULL,
name Utf8 NOT NULL,
duration uint64 NULL,
PRIMARY KEY (id));''')
        await db.commit()
