"""Rate limiting middleware."""
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from typing import Callable, Dict, Any, Awaitable
from collections import defaultdict
from datetime import datetime, timedelta


class RateLimitMiddleware(BaseMiddleware):
    """Middleware to rate limit user requests."""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_requests = defaultdict(list)
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        now = datetime.now()
        
        # Clean old requests
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if now - req_time < timedelta(seconds=self.window_seconds)
        ]
        
        # Check rate limit
        if len(self.user_requests[user_id]) >= self.max_requests:
            if isinstance(event, Message):
                await event.answer("Братан, не тормози! Слишком много запросов. Подожди минутку 💨")
            elif isinstance(event, CallbackQuery):
                await event.answer("Братан, не тормози! Слишком много запросов. Подожди минутку 💨", show_alert=True)
            return
        
        # Add current request
        self.user_requests[user_id].append(now)
        
        return await handler(event, data)
