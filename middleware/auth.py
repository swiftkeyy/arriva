"""Authentication middleware."""
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from typing import Callable, Dict, Any, Awaitable
import config


class AuthMiddleware(BaseMiddleware):
    """Middleware to check admin privileges."""
    
    def __init__(self, admin_ids: list[int]):
        self.admin_ids = admin_ids
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Check if command requires admin
        if isinstance(event, Message):
            if event.text and event.text.startswith('/'):
                admin_commands = [
                    '/admin', '/products', '/addproduct', '/orders', '/meetings',
                    '/referrals', '/stats', '/broadcast', '/settings', '/user',
                    '/kaspi_paid', '/meeting_done', '/lowstock', '/top', '/export'
                ]
                
                command = event.text.split()[0]
                if command in admin_commands:
                    if event.from_user.id not in self.admin_ids:
                        await event.answer(config.ERROR_MESSAGES["access_denied"])
                        return
                    
                    # Add admin flag to data
                    data['is_admin'] = True
        elif isinstance(event, CallbackQuery):
            # For callback queries, check if it's an admin action
            if event.data and event.data.startswith('admin_'):
                if event.from_user.id not in self.admin_ids:
                    await event.answer(config.ERROR_MESSAGES["access_denied"], show_alert=True)
                    return
                
                # Add admin flag to data
                data['is_admin'] = True
        
        return await handler(event, data)
