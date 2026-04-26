"""Cart handlers."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import cart, products
from keyboards.customer import get_cart_keyboard, get_main_menu_keyboard
from database.db_instance import get_db
import config

router = Router()


class CartStates(StatesGroup):
    waiting_for_custom_quantity = State()


@router.callback_query(F.data.startswith("qty_"))
async def handle_quantity_selection(callback: CallbackQuery, state: FSMContext):
    """Handle quantity selection."""
    parts = callback.data.split("_")
    product_id = int(parts[1])
    flavor = parts[2]
    quantity_str = parts[3]
    
    db = get_db()
    
    if quantity_str == "custom":
        await state.update_data(product_id=product_id, flavor=flavor)
        await state.set_state(CartStates.waiting_for_custom_quantity)
        await callback.message.answer("Братан, введи количество (от 1 до 10): 💨")
        await callback.answer()
        return
    
    quantity = int(quantity_str)
    
    # Get product
    product = await products.get_product_by_id(db, product_id)
    
    if product['stock_quantity'] < quantity:
        await callback.answer(
            config.ERROR_MESSAGES["insufficient_stock"].format(available=product['stock_quantity']),
            show_alert=True
        )
        return
    
    # Get user
    from database import users
    user = await users.get_user_by_telegram_id(db, callback.from_user.id)
    
    # Add to cart
    await cart.add_to_cart(db, user['id'], product_id, flavor, quantity)
    
    # Show cart
    cart_items = await cart.get_user_cart(db, user['id'])
    total = await cart.get_cart_total(db, user['id'])
    
    text = f"""✅ Добавлено в корзину!

{product['name']} — {flavor}
Количество: {quantity} шт
Цена: {product['price'] * quantity}₸

🛒 Всего в корзине: {total}₸

Погнали дальше, братан! 🔥"""
    
    await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard())
    await callback.answer()


@router.message(CartStates.waiting_for_custom_quantity)
async def handle_custom_quantity(message: Message, state: FSMContext):
    """Handle custom quantity input."""
    try:
        quantity = int(message.text)
        if quantity < 1 or quantity > 10:
            raise ValueError()
    except ValueError:
        await message.answer(config.ERROR_MESSAGES["invalid_quantity"])
        return
    
    data = await state.get_data()
    product_id = data['product_id']
    flavor = data['flavor']
    
    db = get_db()
    product = await products.get_product_by_id(db, product_id)
    
    if product['stock_quantity'] < quantity:
        await message.answer(
            config.ERROR_MESSAGES["insufficient_stock"].format(available=product['stock_quantity'])
        )
        return
    
    from database import users
    user = await users.get_user_by_telegram_id(db, message.from_user.id)
    
    await cart.add_to_cart(db, user['id'], product_id, flavor, quantity)
    
    total = await cart.get_cart_total(db, user['id'])
    
    text = f"""✅ Добавлено в корзину!

{product['name']} — {flavor}
Количество: {quantity} шт
Цена: {product['price'] * quantity}₸

🛒 Всего в корзине: {total}₸

Погнали дальше, братан! 🔥"""
    
    await message.answer(text, reply_markup=get_main_menu_keyboard())
    await state.clear()


@router.callback_query(F.data == "view_cart")
async def show_cart(callback: CallbackQuery):
    """Show cart contents."""
    db = get_db()
    
    from database import users
    user = await users.get_user_by_telegram_id(db, callback.from_user.id)
    
    cart_items = await cart.get_user_cart(db, user['id'])
    
    if not cart_items:
        await callback.message.edit_text(
            config.ERROR_MESSAGES["empty_cart"],
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer()
        return
    
    text = "🛒 ТВОЯ КОРЗИНА\n\n"
    total = 0
    
    for item in cart_items:
        text += f"💨 {item['product_name']} — {item['flavor']}\n"
        text += f"   {item['quantity']} шт × {item['unit_price']}₸ = {item['subtotal']}₸\n\n"
        total += item['subtotal']
    
    text += f"💰 ИТОГО: {total}₸\n\nПогнали оформлять, братан! 🔥"
    
    await callback.message.edit_text(text, reply_markup=get_cart_keyboard(has_items=True))
    await callback.answer()


@router.callback_query(F.data == "clear_cart")
async def clear_user_cart(callback: CallbackQuery):
    """Clear cart."""
    db = get_db()
    
    from database import users
    user = await users.get_user_by_telegram_id(db, callback.from_user.id)
    
    await cart.clear_cart(db, user['id'])
    
    await callback.message.edit_text(
        "🗑 Корзина очищена, братан!\n\nПогнали выбирать заново! 💨",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()
