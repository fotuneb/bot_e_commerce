import os
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from typing import Dict
from src.db import DB

router = Router()

# Простая проверка admin по ID (можно расширить через env)
ADMIN_IDS = {int(x) for x in os.getenv('ADMIN_IDS', '1').split(',') if x}


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command(commands=['add_category']))
async def cmd_add_category(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer('Только для админов')
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer('Использование: /add_category <name>')
        return
    name = parts[1]
    try:
        db: DB = DB()
        cid: int = await db.add_category(name)
        logger = __import__('logging').getLogger('handlers.admin')
        logger.info('Admin %s added category %s (id=%s)', message.from_user.id, name, cid)
        await message.answer(f'Категория добавлена id={cid}')
    except Exception:
        logger = __import__('logging').getLogger('handlers.admin')
        logger.exception('Error adding category')
        await message.answer('Не удалось добавить категорию')


@router.message(Command(commands=['add_product']))
async def cmd_add_product(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer('Только для админов')
        return
    # Формат: /add_product <category_id>|<name>|<description>|<price>
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer('Использование: /add_product <category_id>|<name>|<description>|<price>')
        return
    try:
        cat_id, name, desc, price = parts[1].split('|')
        price = float(price)
    except Exception:
        await message.answer('Неверный формат')
        return
    try:
        db: DB = DB()
        pid: int = await db.add_product(int(cat_id), name.strip(), desc.strip(), price, None)
        logger = __import__('logging').getLogger('handlers.admin')
        logger.info('Admin %s added product %s id=%s', message.from_user.id, name.strip(), pid)
        await message.answer(f'Товар добавлен id={pid}')
    except Exception:
        logger = __import__('logging').getLogger('handlers.admin')
        logger.exception('Error adding product')
        await message.answer('Не удалось добавить товар')


@router.message(Command(commands=['edit_product']))
async def cmd_edit_product(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer('Только для админов')
        return
    # Формат: /edit_product <product_id>|<name>|<description>|<price>
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer('Использование: /edit_product <product_id>|<name>|<description>|<price>')
        return
    try:
        pid, name, desc, price = parts[1].split('|')
        pid = int(pid)
        price = float(price)
    except Exception:
        await message.answer('Неверный формат')
        return
    db: DB = DB()
    await db.update_product(pid, name=name.strip(), description=desc.strip(), price=price)
    await message.answer('Товар обновлён')


@router.message(Command(commands=['delete_product']))
async def cmd_delete_product(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer('Только для админов')
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer('Использование: /delete_product <product_id>')
        return
    try:
        pid = int(parts[1])
    except ValueError:
        await message.answer('Неверный product_id')
        return
    db: DB = DB()
    await db.delete_product(pid)
    await message.answer('Товар удалён')


@router.message(Command(commands=['list_orders']))
async def cmd_list_orders(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer('Только для админов')
        return
    try:
        db: DB = DB()
        orders = await db.list_orders()
        if not orders:
            await message.answer('Заказов нет')
            return
        lines = [f"{o['id']}: {o['order_number']} - {o['customer_name']} - {o['status']} - {o['total']}" for o in orders]
        await message.answer('\n'.join(lines))
    except Exception:
        logger = __import__('logging').getLogger('handlers.admin')
        logger.exception('Error listing orders')
        await message.answer('Не удалось получить заказы')


@router.message(Command(commands=['set_status']))
async def cmd_set_status(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer('Только для админов')
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer('Использование: /set_status <order_id> <status>')
        return
    try:
        oid = int(parts[1])
    except ValueError:
        await message.answer('Неверный order_id')
        return
    status = parts[2]
    try:
        db: DB = DB()
        await db.update_order_status(oid, status)
        logger = __import__('logging').getLogger('handlers.admin')
        logger.info('Admin %s set order %s status %s', message.from_user.id, oid, status)
        await message.answer('Статус обновлён')
    except Exception:
        logger = __import__('logging').getLogger('handlers.admin')
        logger.exception('Error setting order status')
        await message.answer('Не удалось обновить статус')
