import aiosqlite

table_name = 'Clients'

async def create_clients():
    async with aiosqlite.connect(DB_NAME) as db:

# Добавил свою модельку заказов
# Может не заработать, т.к. скрипт написан под YQL
        await db.execute(f'''
CREATE TABLE IF NOT EXISTS Orders (
id uint64 NOT NULL,
createDate Datetime NOT NULL,
planDate Datetime NOT NULL,
dueDate Datetime NULL,
description Utf8 NOT NULL,
clientId uint64 NOT NULL,
statusId uint64 NOT NULL,
workTypeId uint64 NULL,
PRIMARY KEY (id));''')
        await db.commit()