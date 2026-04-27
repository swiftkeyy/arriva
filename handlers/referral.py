"""Referral handlers."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database import users
from database.referrals import get_referral_stats
from keyboards.customer import get_main_menu_keyboard
from database.db_instance import get_db

router = Router()


@router.message(Command("referral"))
@router.callback_query(F.data == "view_referral")
async def show_referral(event):
    """Show referral program info."""
    if isinstance(event, CallbackQuery):
        message = event.message
        db = get_db()
        user_id = event.from_user.id
    else:
        message = event
        db = get_db()
        user_id = event.from_user.id
    
    user = await users.get_user_by_telegram_id(db, user_id)
    stats = await get_referral_stats(db, user['id'])
    
    bot_username = (await message.bot.me()).username
    referral_link = f"https://t.me/{bot_username}?start={user['referral_code']}"
    
    text = f"""💎 РЕФЕРАЛЬНАЯ ПРОГРАММА

Приведи друга — получи 500₸ на Kaspi!

🔗 Твоя ссылка:
{referral_link}

📊 Твоя статистика:
👥 Приглашено друзей: {stats['referee_count']}
💰 Заработано: {stats['total_bonuses']}₸

Как это работает:
1. Отправь ссылку другу
2. Друг регистрируется и делает заказ
3. Ты получаешь 500₸ на Kaspi

Погнали зарабатывать, братан!"""
    
    if isinstance(event, CallbackQuery):
        await message.edit_text(text, reply_markup=get_main_menu_keyboard())
        await event.answer()
    else:
        await message.answer(text, reply_markup=get_main_menu_keyboard())
