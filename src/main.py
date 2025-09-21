import logging
import logging.handlers
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import Message
from src.db import DB, init_db

from src.handlers import catalog, cart, order, admin

API_TOKEN = '<PUT_YOUR_TOKEN_HERE>'

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
    bot = Bot(token=API_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(order.router)

    @dp.message(Command(commands=['start']))
    async def cmd_start(message: Message):
        await message.answer('Привет! Это демонстрационный магазин. Используйте /catalog')

    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info('Bot stopped')
