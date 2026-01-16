import aiosqlite

table_name = 'Clients'

async def create_clients():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(f'''CREATE TABLE IF NOT EXISTS {DB_NAME} (user_id INTEGER PRIMARY KEY, question_index INTEGER, records_book VARCHAR(255))''')
        await db.commit()
