from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from database import db


class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        return await db.is_admin(event.from_user.id)
