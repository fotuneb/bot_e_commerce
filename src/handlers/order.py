from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
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


@router.callback_query()
async def order_start(cb: CallbackQuery, state: FSMContext):
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
    txt = f"Проверьте данные:\nИмя: {data.get('name')}\nТел: {data.get('phone')}\nАдрес: {data.get('address')}\n\nПодтвердите: /confirm или /cancel"
    await state.set_state(OrderStates.confirm)
    await message.answer(txt)


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


@router.message(Command(commands=['cancel']))
async def cancel_order(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Оформление заказа отменено')
