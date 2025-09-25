import logging
import logging.handlers
import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import Message
from src.db import DB, init_db

from src.handlers import catalog, cart, order, admin

# Load .env if python-dotenv is available (optional)
try:
    from dotenv import load_dotenv

    # load .env from project root if present
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
except Exception:
    # dotenv not installed or failed to load; ignore and rely on environment variables
    pass

# Prefer environment variable; fallback to placeholder (will raise if not set)
API_TOKEN = os.getenv('API_TOKEN', '<PUT_YOUR_TOKEN_HERE>')

# Logging setup: console + rotating file
logger = logging.getLogger('bot')
logger.setLevel(logging.INFO)
fmt = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(fmt)
fh = logging.handlers.RotatingFileHandler('bot.log', maxBytes=2_000_000, backupCount=3, encoding='utf-8')
fh.setFormatter(fmt)
logger.addHandler(ch)
logger.addHandler(fh)


async def main():
    await init_db()
    if not API_TOKEN or API_TOKEN == '<PUT_YOUR_TOKEN_HERE>':
        logger = logging.getLogger('bot')
        logger.error('API_TOKEN is not set. Please set API_TOKEN in environment or .env file.')
        raise SystemExit('API_TOKEN is missing')

    bot = Bot(token=API_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(order.router)
    dp.include_router(admin.router)

    @dp.message(Command(commands=['start']))
    async def cmd_start(message: Message):
        await message.answer('Привет! Это демонстрационный магазин. Используйте /catalog')

    @dp.message(Command(commands=['admin']))
    async def cmd_admin(message: Message):
        try:
            if admin.is_admin(message.from_user.id):
                await message.answer(
                    'Admin commands:\n'
                    '/add_category <name>\n'
                    '/add_product <category_id>|<name>|<description>|<price>\n'
                    '/edit_product <product_id>|<name>|<description>|<price>\n'
                    '/delete_product <product_id>\n'
                    '/list_orders\n'
                    '/set_status <order_id> <status>'
                )
            else:
                await message.answer('Только для админов')
        except Exception:
            logger = __import__('logging').getLogger('main')
            logger.exception('Error in /admin handler')
            await message.answer('Ошибка')

    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info('Bot stopped')
