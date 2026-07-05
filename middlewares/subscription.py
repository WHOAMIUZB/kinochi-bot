from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable

from database import db
from utils.subscription import get_unsubscribed_channels
from keyboards.user_kb import subscribe_kb

SUBSCRIBE_TEXT = (
    "⛔️ Botdan foydalanish uchun quyidagi kanal/guruhlarga obuna bo'ling, "
    "so'ng \"✅ Obuna bo'ldim\" tugmasini bosing."
)


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        user = event.from_user
        if user is None or user.is_bot:
            return await handler(event, data)

        # check_sub tugmasi o'zi tekshiruv qiladi, middleware'da bloklanmasin
        if isinstance(event, CallbackQuery) and event.data == "check_sub":
            return await handler(event, data)

        if await db.is_admin(user.id):
            return await handler(event, data)

        bot = data["bot"]
        unsubscribed = await get_unsubscribed_channels(bot, user.id)
        if unsubscribed:
            if isinstance(event, Message):
                await event.answer(SUBSCRIBE_TEXT, reply_markup=subscribe_kb(unsubscribed))
            else:
                await event.answer("Avval kanallarga obuna bo'ling!", show_alert=True)
                try:
                    await event.message.edit_reply_markup(reply_markup=subscribe_kb(unsubscribed))
                except Exception:
                    pass
            return None

        return await handler(event, data)
