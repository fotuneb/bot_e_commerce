from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from src.db import DB

router = Router()


@router.message(Command(commands=['catalog']))
async def show_categories(message: Message):
    try:
        db = DB()
        cats = await db.list_categories()
        if not cats:
            await message.answer('Категории пусты.')
            return
        rows = []
        for c in cats:
            rows.append([InlineKeyboardButton(text=c['name'], callback_data=f'cat:{c["id"]}')])
        kb = InlineKeyboardMarkup(inline_keyboard=rows)
        await message.answer('Выберите категорию:', reply_markup=kb)
    except Exception:
        logger = __import__('logging').getLogger('handlers.catalog')
        logger.exception('Error showing categories')
        await message.answer('Произошла ошибка при получении категорий. Попробуйте позже.')


@router.callback_query()
async def category_cb(query: CallbackQuery):
    try:
        data = query.data or ''
        if not data.startswith('cat:'):
            return
        cid = int(data.split(':', 1)[1])
        db = DB()
        products = await db.list_products_by_category(cid)
        if not products:
            await query.message.answer('Нет товаров в категории')
            await query.answer()
            return
        rows = []
        for p in products:
            rows.append([InlineKeyboardButton(text=f"{p['name']} — {p['price']}", callback_data=f'prod:{p["id"]}')])
        kb = InlineKeyboardMarkup(inline_keyboard=rows)
        await query.message.answer('Товары:', reply_markup=kb)
        await query.answer()
    except Exception:
        logger = __import__('logging').getLogger('handlers.catalog')
        logger.exception('Error listing products')
        await query.answer('Ошибка при получении товаров', show_alert=True)


@router.callback_query()
async def product_cb(query: CallbackQuery):
    data = query.data or ''
    try:
        if data.startswith('prod:'):
            pid = int(data.split(':', 1)[1])
            db = DB()
            p = await db.get_product(pid)
            if not p:
                await query.answer('Товар не найден', show_alert=True)
                return
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='В корзину', callback_data=f'add:{pid}'), InlineKeyboardButton(text='Назад', callback_data=f'back_cat:{p["category_id"]}')]])
            txt = f"{p['name']}\n{p.get('description','')}\nЦена: {p['price']}"
            await query.message.answer(txt, reply_markup=kb)
            await query.answer()
    except Exception:
        logger = __import__('logging').getLogger('handlers.catalog')
        logger.exception('Error showing product')
        await query.answer('Ошибка при получении товара', show_alert=True)


@router.callback_query()
async def add_to_cart_cb(query: CallbackQuery):
    data = query.data or ''
    try:
        if data.startswith('add:'):
            pid = int(data.split(':', 1)[1])
            db = DB()
            cart = await db.get_cart(query.from_user.id)
            cart[str(pid)] = int(cart.get(str(pid), 0)) + 1
            await db.set_cart(query.from_user.id, cart)
            await query.answer('Добавлено в корзину')
    except Exception:
        logger = __import__('logging').getLogger('handlers.catalog')
        logger.exception('Error adding to cart')
        await query.answer('Не удалось добавить товар в корзину', show_alert=True)

