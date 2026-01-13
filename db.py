import aiosqlite


async def create_tables(DB_NAME):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(f'''CREATE TABLE IF NOT EXISTS {DB_NAME} (user_id INTEGER PRIMARY KEY, question_index INTEGER, records_book VARCHAR(255))''')
        await db.commit()


# async def update_quiz_index(user_id, index, records_book):
#     async with aiosqlite.connect(DB_NAME) as db:
#         await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, question_index, records_book) VALUES (?, ?, ?)', (user_id, index, records_book))
#         await db.commit()


# async def get_quiz_index(user_id):
#     async with aiosqlite.connect(DB_NAME) as db:
#         async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = (?)', (user_id,)) as cursor:
#             results = await cursor.fetchone()
#             if results is not None:
#                 return results[0]
#             else:
#                 return 0


# async def get_records_book(user_id):
#     async with aiosqlite.connect(DB_NAME) as db:
#         async with db.execute('SELECT records_book FROM quiz_state WHERE user_id = (?)', (user_id,)) as cursor:
#             results = await cursor.fetchone()
#             if results is not None:
#                 return results[0]
#             else:
#                 return 0
