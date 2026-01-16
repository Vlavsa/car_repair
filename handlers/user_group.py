from string import punctuation

from aiogram import F, types, Router

from filters.filters_type import ChatTypeFilter

user_group_router = Router()
user_group_router.message.filter(ChatTypeFilter(['group', 'supergroup']))
user_group_router.edited_message.filter(ChatTypeFilter(['group', 'supergroup']))


restricted_words = {'сука', 'блять', 'пидор'}

def clean_text(text: str):
    return text.translate(str.maketrans('', '', punctuation))


@user_group_router.edited_message()
@user_group_router.message()
async def cleaner(message: types.Message):
    if restricted_words.intersection(clean_text(message.text.lower()).split()):
        ban_user = message.from_user.username if message.from_user.username else message.from_user.id
        await message.answer(f'@{ban_user} соблюдайте порядок в чате!')
        await message.delete()
        # await message.chat.ban(message.from_user.id)