import asyncio
from src.db import DB, init_db


async def seed():
    await init_db()
    db = DB()
    cat_id = await db.add_category('Смартфоны')
    await db.add_product(cat_id, 'Телефон A', 'Описание A', 199.99, None)
    await db.add_product(cat_id, 'Телефон B', 'Описание B', 299.99, None)
    print('Seed done')


if __name__ == '__main__':
    asyncio.run(seed())
