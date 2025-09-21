import asyncio
from src.utils import gen_order_number
from src.db import DB, init_db


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_gen_order_number():
    n = gen_order_number()
    assert n.startswith('ORD-') and len(n) > 4


def test_cart_set_get(tmp_path):
    db_path = tmp_path / 'test2.db'
    run(init_db(str(db_path)))
    db = DB(str(db_path))
    user_id = 123
    items = {"1": 2, "2": 1}
    run(db.set_cart(user_id, items))
    loaded = run(db.get_cart(user_id))
    assert loaded == items


def test_cart_total_and_order(tmp_path):
    db_path = tmp_path / 'test3.db'
    run(init_db(str(db_path)))
    db = DB(str(db_path))
    cid = run(db.add_category('C'))
    p1 = run(db.add_product(cid, 'A', 'd', 5.0, None))
    p2 = run(db.add_product(cid, 'B', 'd', 3.0, None))
    user_id = 42
    items = {str(p1): 2, str(p2): 1}
    run(db.set_cart(user_id, items))
    total = run(db.cart_total(user_id))
    assert total == 13.0
    order_num = 'TEST-1'
    oid = run(db.create_order(order_num, user_id, 'Name', 'Phone', 'Addr', 'std', items, total))
    assert isinstance(oid, int)
    orders = run(db.list_orders())
    assert any(o['order_number'] == order_num for o in orders)


def test_empty_cart_behavior(tmp_path):
    db_path = tmp_path / 'test_empty.db'
    run(init_db(str(db_path)))
    db = DB(str(db_path))
    # user with empty cart
    user_id = 999
    total = run(db.cart_total(user_id))
    assert total == 0.0

