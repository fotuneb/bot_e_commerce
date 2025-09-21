from db import DB


class AdminAPI:
    def __init__(self, db: DB):
        self.db = db

    async def add_category(self, name: str):
        return await self.db.add_category(name)

    async def add_product(self, category_id: int, name: str, description: str, price: float, photo: str = None):
        return await self.db.add_product(category_id, name, description, price, photo)
