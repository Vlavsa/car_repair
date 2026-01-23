import aiosqlite

table_name = 'Clients'

async def create_clients():
    async with aiosqlite.connect(DB_NAME) as db:
#         await db.execute(f'''
# CREATE TABLE IF NOT EXISTS {DB_NAME} (
# user_id INTEGER PRIMARY KEY, 
# question_index INTEGER, 
# records_book VARCHAR(255))''')

# Добавил свою модельку клиентов
# Может не заработать, т.к. скрипт написан под YQL
        await db.execute(f'''
CREATE TABLE IF NOT EXISTS Clients (
id uint64 NOT NULL,
name Utf8 NOT NULL,
phone Utf8 NOT NULL,
username Utf8 NOT NULL,
PRIMARY KEY (id));''')
        await db.commit()
