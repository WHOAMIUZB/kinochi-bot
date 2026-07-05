from aiogram import Bot
from database import db

NOT_MEMBER_STATUSES = {"left", "kicked"}


async def get_unsubscribed_channels(bot: Bot, user_id: int):
    """Foydalanuvchi obuna bo'lmagan majburiy kanallar ro'yxatini qaytaradi."""
    channels = await db.get_channels()
    unsubscribed = []
    for ch in channels:
        _id, chat_id, title, username, invite_link, chat_type = ch
        try:
            member = await bot.get_chat_member(chat_id, user_id)
            if member.status in NOT_MEMBER_STATUSES:
                unsubscribed.append(ch)
        except Exception:
            # Bot kanalda admin emas yoki boshqa xatolik - xavfsizlik uchun obuna bo'lmagan deb hisoblaymiz
            unsubscribed.append(ch)
    return unsubscribed


async def is_bot_admin_in_chat(bot: Bot, chat_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, bot.id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False
