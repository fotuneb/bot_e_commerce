from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.db import DB
from src.utils import gen_order_number

router = Router()


class OrderStates(StatesGroup):
    name = State()
    phone = State()
    address = State()
    confirm = State()


@router.callback_query(lambda q: (q.data or '') == 'order:start')
async def order_start(cb: CallbackQuery, state: FSMContext):
    # Debug print
    print(f'order_start CALLBACK RECEIVED: data={getattr(cb, "data", None)} from={getattr(cb.from_user, "id", None)}')
    if cb.data != 'order:start':
        return
    try:
        await state.set_state(OrderStates.name)
        await cb.message.answer('Пожалуйста, пришлите ваше имя:')
        await cb.answer()
    except Exception:
        logger = __import__('logging').getLogger('handlers.order')
        logger.exception('Error starting order')
        await cb.answer('Не удалось начать оформление заказа', show_alert=True)


@router.message(OrderStates.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(OrderStates.phone)
    await message.answer('Отлично, теперь пришлите телефон:')


@router.message(OrderStates.phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(OrderStates.address)
    await message.answer('Укажите адрес доставки:')


@router.message(OrderStates.address)
async def process_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    data = await state.get_data()
    txt = f"Проверьте данные:\nИмя: {data.get('name')}\nТел: {data.get('phone')}\nАдрес: {data.get('address')}"
    await state.set_state(OrderStates.confirm)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Подтвердить', callback_data='order:confirm'), InlineKeyboardButton(text='Отмена', callback_data='order:cancel')]
    ])
    await message.answer(txt, reply_markup=kb)


@router.message(Command(commands=['confirm']))
async def confirm_order(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        db = DB()
        cart = await db.get_cart(message.from_user.id)
        if not cart:
            await message.answer('Ваша корзина пуста')
            await state.clear()
            return
        total = await db.cart_total(message.from_user.id)
        order_number = gen_order_number()
        await db.create_order(order_number, message.from_user.id, data.get('name',''), data.get('phone',''), data.get('address',''), 'standard', cart, total)
        await db.clear_cart(message.from_user.id)
        await message.answer(f'Заказ подтверждён. Номер: {order_number}')
        await state.clear()
    except Exception:
        logger = __import__('logging').getLogger('handlers.order')
        logger.exception('Error confirming order')
        await message.answer('Не удалось подтвердить заказ. Попробуйте позже.')
        await state.clear()


@router.callback_query(lambda q: (q.data or '') == 'order:confirm')
async def order_confirm_cb(cb: CallbackQuery, state: FSMContext):
    try:
        # reuse the same logic as confirm_order
        data = await state.get_data()
        db = DB()
        cart = await db.get_cart(cb.from_user.id)
        if not cart:
            await cb.message.answer('Ваша корзина пуста')
            await state.clear()
            await cb.answer()
            return
        total = await db.cart_total(cb.from_user.id)
        order_number = gen_order_number()
        await db.create_order(order_number, cb.from_user.id, data.get('name',''), data.get('phone',''), data.get('address',''), 'standard', cart, total)
        await db.clear_cart(cb.from_user.id)
        await cb.message.answer(f'Заказ подтверждён. Номер: {order_number}')
        await state.clear()
        await cb.answer()
    except Exception:
        logger = __import__('logging').getLogger('handlers.order')
        logger.exception('Error confirming order (callback)')
        await cb.answer('Не удалось подтвердить заказ. Попробуйте позже.', show_alert=True)


@router.callback_query(lambda q: (q.data or '') == 'order:cancel')
async def order_cancel_cb(cb: CallbackQuery, state: FSMContext):
    try:
        await state.clear()
        await cb.message.answer('Оформление заказа отменено')
        await cb.answer()
    except Exception:
        logger = __import__('logging').getLogger('handlers.order')
        logger.exception('Error cancelling order (callback)')
        await cb.answer('Не удалось отменить оформление', show_alert=True)


@router.message(Command(commands=['cancel']))
async def cancel_order(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Оформление заказа отменено')
