import time
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable

THROTTLE_SECONDS = 0.7


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self):
        self.last_call: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        user = event.from_user
        if user:
            now = time.monotonic()
            last = self.last_call.get(user.id, 0)
            if now - last < THROTTLE_SECONDS:
                return None
            self.last_call[user.id] = now
        return await handler(event, data)
