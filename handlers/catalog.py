"""Catalog handlers."""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from database import products
from keyboards.customer import get_catalog_keyboard, get_product_details_keyboard, get_quantity_keyboard
from database.db_instance import get_db

router = Router()


@router.callback_query(F.data == "view_catalog")
async def show_catalog(callback: CallbackQuery):
    """Show product catalog."""
    db = get_db()
    available_products = await products.get_available_products(db)
    
    if not available_products:
        await callback.message.edit_text(
            "Братан, сейчас все раскупили! 😔\nНовый завоз скоро, следи за обновлениями 🔥"
        )
        await callback.answer()
        return
    
    text = "🔥 КАТАЛОГ ARRIVA SHOP KZ\n\nВыбирай, братан! Все позиции в наличии 💨\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_catalog_keyboard(available_products)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product_"))
async def show_product_details(callback: CallbackQuery):
    """Show product details."""
    db = get_db()
    product_id = int(callback.data.split("_")[1])
    
    product = await products.get_product_by_id(db, product_id)
    
    if not product or product['stock_quantity'] == 0:
        await callback.answer("Братан, этого уже нет в наличии! 😔", show_alert=True)
        return
    
    text = f"""🔥 {product['name']}

💰 Цена: {product['price']}₸
📦 В наличии: {product['stock_quantity']} шт
💨 Вкусы:

Выбирай вкус, братан! Погнали! 🔥"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_product_details_keyboard(product_id, product['flavors'])
    )
    await callback.answer()


@router.callback_query(F.data.startswith("flavor_"))
async def select_flavor(callback: CallbackQuery, state: FSMContext):
    """Handle flavor selection."""
    parts = callback.data.split("_", 2)
    product_id = int(parts[1])
    flavor = parts[2]
    
    db = get_db()
    product = await products.get_product_by_id(db, product_id)
    
    text = f"""💨 {product['name']} — {flavor}

Сколько берём, братан? 🔥"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_quantity_keyboard(product_id, flavor)
    )
    await callback.answer()
