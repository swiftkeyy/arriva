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


@router.callback_query(F.data.startswith("product_") & ~F.data.startswith("product_manage_") & ~F.data.startswith("product_delete_") & ~F.data.startswith("product_price_") & ~F.data.startswith("product_stock_") & ~F.data.startswith("product_flavors_"))
async def show_product_details(callback: CallbackQuery):
    """Show product details."""
    db = get_db()
    product_id = int(callback.data.split("_")[1])

    product = await products.get_product_by_id(db, product_id)

    if not product or product['stock_quantity'] == 0:
        await callback.answer("Братан, этого уже нет в наличии! 😔", show_alert=True)
        return

    from database.products import get_flavor_stock
    flavor_stock = await get_flavor_stock(db, product_id)

    # Показываем только вкусы с остатком > 0
    available_flavors = [(f, flavor_stock.get(f, 0)) for f in product['flavors'] if flavor_stock.get(f, 0) > 0]

    if not available_flavors:
        await callback.answer("Братан, все вкусы закончились! 😔", show_alert=True)
        return

    flavors_text = "\n".join(f"• {f} — {qty} шт" for f, qty in available_flavors)
    text = (
        f"🔥 {product['name']}\n\n"
        f"💰 Цена: {product['price']}₸\n"
        f"💨 Вкусы в наличии:\n{flavors_text}\n\n"
        f"Выбирай вкус, братан! Погнали! 🔥"
    )

    # Клавиатура только с доступными вкусами
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = [
        [InlineKeyboardButton(text=f"💨 {f} ({qty} шт)", callback_data=f"flavor_{product_id}_{f}")]
        for f, qty in available_flavors
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Назад к каталогу", callback_data="view_catalog")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("flavor_"))
async def select_flavor(callback: CallbackQuery, state: FSMContext):
    """Handle flavor selection."""
    # Формат: flavor_{product_id}_{flavor_name}
    parts = callback.data.split("_", 2)
    product_id = int(parts[1])
    flavor = parts[2]

    db = get_db()
    product = await products.get_product_by_id(db, product_id)

    # Получаем остаток по этому вкусу
    from database.products import get_flavor_stock
    flavor_stock = await get_flavor_stock(db, product_id)
    stock = flavor_stock.get(flavor, 0)

    if stock == 0:
        await callback.answer("Этот вкус закончился 😔", show_alert=True)
        return

    text = (
        f"💨 {product['name']} — {flavor}\n\n"
        f"📦 В наличии: {stock} шт\n\n"
        f"Сколько берём, братан? 🔥"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_quantity_keyboard(product_id, flavor)
    )
    await callback.answer()
