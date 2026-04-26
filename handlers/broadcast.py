"""Broadcast handlers."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio

import config
from database import users
from bot import get_db

router = Router()


class BroadcastStates(StatesGroup):
    waiting_for_template = State()
    waiting_for_custom_text = State()
    waiting_for_confirmation = State()


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    """Start broadcast."""
    text = "📢 ВЫБЕРИ ШАБЛОН РАССЫЛКИ:\n\n"
    
    templates = [
        "1. Новинки недели",
        "2. Флеш-скидка",
        "3. Реферальная акция",
        "4. Утренний вайб",
        "5. VIP клиентам",
        "6. Праздничная",
        "7. Реактивация спящих",
        "8. Свой текст"
    ]
    
    text += "\n".join(templates)
    text += "\n\nВведи номер шаблона:"
    
    await state.set_state(BroadcastStates.waiting_for_template)
    await message.answer(text)


@router.message(BroadcastStates.waiting_for_template)
async def process_template_selection(message: Message, state: FSMContext):
    """Process template selection."""
    try:
        choice = int(message.text)
        if choice < 1 or choice > 8:
            raise ValueError()
    except ValueError:
        await message.answer("Братан, введи номер от 1 до 8!")
        return
    
    template_map = {
        1: "new_arrivals",
        2: "flash_sale",
        3: "referral_promotion",
        4: "morning_vibe",
        5: "vip",
        6: "holiday",
        7: "reactivation"
    }
    
    if choice == 8:
        await state.set_state(BroadcastStates.waiting_for_custom_text)
        await message.answer("Введи текст рассылки:")
        return
    
    template_name = template_map[choice]
    broadcast_text = config.BROADCAST_TEMPLATES[template_name]
    
    await state.update_data(text=broadcast_text)
    await state.set_state(BroadcastStates.waiting_for_confirmation)
    
    await message.answer(
        f"📢 ТЕКСТ РАССЫЛКИ:\n\n{broadcast_text}\n\n"
        f"Отправить всем пользователям? (да/нет)"
    )


@router.message(BroadcastStates.waiting_for_custom_text)
async def process_custom_text(message: Message, state: FSMContext):
    """Process custom broadcast text."""
    await state.update_data(text=message.text)
    await state.set_state(BroadcastStates.waiting_for_confirmation)
    
    await message.answer(
        f"📢 ТЕКСТ РАССЫЛКИ:\n\n{message.text}\n\n"
        f"Отправить всем пользователям? (да/нет)"
    )


@router.message(BroadcastStates.waiting_for_confirmation)
async def process_confirmation(message: Message, state: FSMContext):
    """Process confirmation and send broadcast."""
    if message.text.lower() not in ['да', 'yes', 'д', 'y']:
        await message.answer("❌ Рассылка отменена")
        await state.clear()
        return
    
    data = await state.get_data()
    broadcast_text = data['text']
    
    db = get_db()
    
    # Get all users
    cursor = await db.execute("SELECT telegram_id FROM users WHERE is_blocked = 0")
    all_users = await cursor.fetchall()
    
    await message.answer(f"📤 Начинаю рассылку для {len(all_users)} пользователей...")
    
    success = 0
    failed = 0
    
    for user in all_users:
        try:
            await message.bot.send_message(user[0], broadcast_text)
            success += 1
            await asyncio.sleep(0.05)  # Rate limiting
        except Exception:
            failed += 1
    
    await message.answer(
        f"✅ Рассылка завершена!\n\n"
        f"✅ Отправлено: {success}\n"
        f"❌ Ошибок: {failed}"
    )
    
    await state.clear()
