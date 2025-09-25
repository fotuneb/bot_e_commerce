from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from src.db import DB

router = Router()


@router.message(Command(commands=['cart']))
async def show_cart(message: Message):
    try:
        db = DB()
        cart = await db.get_cart(message.from_user.id)
        if not cart:
            await message.answer('Ваша корзина пуста')
            return
        lines = []
        for pid_str, qty in cart.items():
            prod = await db.get_product(int(pid_str))
            if prod:
                lines.append(f"{prod['name']} x{qty} — {prod['price'] * int(qty)}")
        total = await db.cart_total(message.from_user.id)
        rows = [[InlineKeyboardButton(text='Оформить заказ', callback_data='order:start'), InlineKeyboardButton(text='Очистить корзину', callback_data='cart:clear')]]
        kb = InlineKeyboardMarkup(inline_keyboard=rows)
        await message.answer('\n'.join(lines) + f"\n\nИтого: {total}", reply_markup=kb)
    except Exception:
        logger = __import__('logging').getLogger('handlers.cart')
        logger.exception('Error showing cart')
        await message.answer('Не удалось получить корзину. Попробуйте позже.')



@router.callback_query(lambda q: any((q.data or '').startswith(p) for p in ('cart:', 'inc:', 'dec:', 'remove:')))
async def cart_cb(query: CallbackQuery):
    data = query.data or ''
    # Debug print
    print(f'cart_cb CALLBACK RECEIVED: data={data} from={getattr(query.from_user, "id", None)}')
    db = DB()
    if data == 'cart:clear':
        await db.clear_cart(query.from_user.id)
        await query.message.answer('Корзина очищена')
        await query.answer()
        return
    if data.startswith('inc:'):
        pid = data.split(':', 1)[1]
        cart = await db.get_cart(query.from_user.id)
        cart[pid] = int(cart.get(pid, 0)) + 1
        await db.set_cart(query.from_user.id, cart)
        await query.answer('Количество увеличено')
        return
    if data.startswith('dec:'):
        pid = data.split(':', 1)[1]
        cart = await db.get_cart(query.from_user.id)
        if cart.get(pid):
            cart[pid] = int(cart.get(pid, 1)) - 1
            if cart[pid] <= 0:
                del cart[pid]
            await db.set_cart(query.from_user.id, cart)
        await query.answer('Количество уменьшено')
        return
    if data.startswith('remove:'):
        pid = data.split(':', 1)[1]
        cart = await db.get_cart(query.from_user.id)
        if pid in cart:
            del cart[pid]
            await db.set_cart(query.from_user.id, cart)
        await query.answer('Товар удалён')
        return
    
    # общая обработка ошибок
    try:
        pass
    except Exception:
        logger = __import__('logging').getLogger('handlers.cart')
        logger.exception('Error in cart callback')
        await query.answer('Произошла ошибка при изменении корзины', show_alert=True)
