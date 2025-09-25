import aiosqlite
import asyncio
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

import os

# Allow overriding DB path via environment (useful for Docker)
DB_PATH = os.getenv('DB_PATH', 'bot_store.db')

CREATE_SQL = [
    """
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        photo TEXT,
        FOREIGN KEY(category_id) REFERENCES categories(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS carts (
        user_id INTEGER PRIMARY KEY,
        items TEXT -- JSON encoded {product_id: qty}
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE,
        user_id INTEGER,
        customer_name TEXT,
        phone TEXT,
        address TEXT,
        delivery_method TEXT,
        items TEXT,
        total REAL,
        status TEXT DEFAULT 'new'
    )
    """,
]


async def init_db(path: str = DB_PATH) -> None:
    """Initialize database schema.

    Args:
        path: Path to sqlite database file.
    """
    async with aiosqlite.connect(path) as db:
        for sql in CREATE_SQL:
            await db.execute(sql)
        await db.commit()
    logger.info('Database initialized')




class DB:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        self._lock = asyncio.Lock()

    async def _execute(self, sql: str, params: tuple = ()) -> aiosqlite.Cursor:  # simple helper
        async with self._lock:
            async with aiosqlite.connect(self.path) as db:
                try:
                    cur = await db.execute(sql, params)
                    await db.commit()
                    return cur
                except Exception as e:
                    logger.exception('DB execute failed: %s | %s', sql, params)
                    raise

    async def fetchall(self, sql: str, params: tuple = ()) -> List[aiosqlite.Row]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            try:
                cur = await db.execute(sql, params)
                rows = await cur.fetchall()
                return rows
            except Exception:
                logger.exception('DB fetchall failed: %s | %s', sql, params)
                raise

    # Categories
    async def list_categories(self) -> List[Dict[str, Any]]:
        rows = await self.fetchall('SELECT id, name FROM categories')
        return [dict(r) for r in rows]

    async def add_category(self, name: str) -> int:
        """Add a category and return its id."""
        cur = await self._execute('INSERT INTO categories(name) VALUES (?)', (name,))
        cid = cur.lastrowid
        logger.info('Category added: %s (id=%s)', name, cid)
        return cid

    # Products
    async def list_products_by_category(self, category_id: int) -> List[Dict[str, Any]]:
        """Return list of products for a category."""
        rows = await self.fetchall('SELECT * FROM products WHERE category_id = ?', (category_id,))
        return [dict(r) for r in rows]

    async def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Return product dict or None if not found."""
        rows = await self.fetchall('SELECT * FROM products WHERE id = ?', (product_id,))
        return dict(rows[0]) if rows else None

    async def get_products(self, product_ids: List[int]) -> List[Dict[str, Any]]:
        """Return multiple products by ids."""
        if not product_ids:
            return []
        qmarks = ','.join(['?'] * len(product_ids))
        rows = await self.fetchall(f'SELECT * FROM products WHERE id IN ({qmarks})', tuple(product_ids))
        return [dict(r) for r in rows]

    async def add_product(self, category_id: int, name: str, description: str, price: float, photo: Optional[str] = None) -> int:
        """Insert a new product and return its id."""
        cur = await self._execute(
            'INSERT INTO products(category_id,name,description,price,photo) VALUES (?,?,?,?,?)',
            (category_id, name, description, price, photo),
        )
        pid = cur.lastrowid
        logger.info('Product added: %s (id=%s) in category %s price=%s', name, pid, category_id, price)
        return pid

    async def update_product(self, product_id: int, **fields) -> None:
        """Update product fields (name, description, price, photo, category_id)."""
        # fields: name, description, price, photo, category_id
        allowed = ['name', 'description', 'price', 'photo', 'category_id']
        set_parts = []
        params = []
        for k, v in fields.items():
            if k in allowed:
                set_parts.append(f"{k} = ?")
                params.append(v)
        if not set_parts:
            return
        params.append(product_id)
        sql = f"UPDATE products SET {', '.join(set_parts)} WHERE id = ?"
        await self._execute(sql, tuple(params))
        logger.info('Product %s updated fields: %s', product_id, list(fields.keys()))

    async def delete_product(self, product_id: int) -> None:
        """Delete product by id."""
        await self._execute('DELETE FROM products WHERE id = ?', (product_id,))
        logger.info('Product %s deleted', product_id)

    # Cart (simple JSON storage)
    async def get_cart(self, user_id: int) -> Dict[int, int]:
        """Return user cart as dict product_id->qty. Empty dict if none."""
        rows = await self.fetchall('SELECT items FROM carts WHERE user_id = ?', (user_id,))
        if not rows:
            return {}
        import json
        return json.loads(rows[0]['items'])

    async def set_cart(self, user_id: int, items: Dict[int, int]) -> None:
        """Set user cart (overwrites)."""
        import json
        items_json = json.dumps(items)
        rows = await self.fetchall('SELECT user_id FROM carts WHERE user_id = ?', (user_id,))
        if rows:
            await self._execute('UPDATE carts SET items = ? WHERE user_id = ?', (items_json, user_id))
        else:
            await self._execute('INSERT INTO carts(user_id, items) VALUES (?,?)', (user_id, items_json))

    async def clear_cart(self, user_id: int) -> None:
        """Remove cart entry for user."""
        await self._execute('DELETE FROM carts WHERE user_id = ?', (user_id,))

    async def cart_total(self, user_id: int) -> float:
        """Calculate total price for user's cart."""
        cart = await self.get_cart(user_id)
        if not cart:
            return 0.0
        prod_ids = [int(pid) for pid in cart.keys()]
        prods = await self.get_products(prod_ids)
        price_map = {p['id']: p['price'] for p in prods}
        total = 0.0
        for pid_str, qty in cart.items():
            pid = int(pid_str)
            price = price_map.get(pid, 0.0)
            total += price * int(qty)
        return total

    # Orders
    async def create_order(self, order_number: str, user_id: int, customer_name: str, phone: str, address: str, delivery_method: str, items: Dict[int, int], total: float) -> int:
        """Create an order record and return its id."""
        import json
        items_json = json.dumps(items)
        cur = await self._execute(
            'INSERT INTO orders(order_number,user_id,customer_name,phone,address,delivery_method,items,total) VALUES (?,?,?,?,?,?,?,?)',
            (order_number, user_id, customer_name, phone, address, delivery_method, items_json, total),
        )
        oid = cur.lastrowid
        logger.info('Order created: %s id=%s user=%s total=%s', order_number, oid, user_id, total)
        return oid

    async def list_orders(self) -> List[Dict[str, Any]]:
        """List orders ordered by most recent."""
        rows = await self.fetchall('SELECT * FROM orders ORDER BY id DESC')
        return [dict(r) for r in rows]

    async def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Return single order by id or None."""
        rows = await self.fetchall('SELECT * FROM orders WHERE id = ?', (order_id,))
        return dict(rows[0]) if rows else None

    async def update_order_status(self, order_id: int, status: str) -> None:
        """Change order status."""
        await self._execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
        logger.info('Order %s status changed to %s', order_id, status)
