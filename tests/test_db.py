import asyncio
import os
import tempfile

from src.db import DB, init_db


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_init_and_category_product_lifecycle(tmp_path):
    db_path = tmp_path / 'test.db'
    # init db
    run(init_db(str(db_path)))
    db = DB(str(db_path))
    # add category
    cat_id = run(db.add_category('Тест'))
    assert isinstance(cat_id, int)
    # add product
    pid = run(db.add_product(cat_id, 'P', 'desc', 10.5, None))
    assert isinstance(pid, int)
    prod = run(db.get_product(pid))
    assert prod['name'] == 'P'

