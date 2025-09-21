import asyncio

from src.db import DB, init_db


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_admin_db_ops(tmp_path):
    db_path = tmp_path / 'adm.db'
    run(init_db(str(db_path)))
    db = DB(str(db_path))
    cid = run(db.add_category('X'))
    pid = run(db.add_product(cid, 'Prod', 'd', 1.0, None))
    # create order
    items = {str(pid): 1}
    oid = run(db.create_order('ON1', 1, 'C', 'P', 'A', 'std', items, 1.0))
    assert oid
    orders = run(db.list_orders())
    assert any(o['order_number'] == 'ON1' for o in orders)
    run(db.update_order_status(oid, 'shipped'))
    o = run(db.get_order(oid))
    assert o['status'] == 'shipped'


def test_edit_and_delete_product(tmp_path):
    db_path = tmp_path / 'adm2.db'
    run(init_db(str(db_path)))
    db = DB(str(db_path))
    cid = run(db.add_category('Y'))
    pid = run(db.add_product(cid, 'Old', 'd', 2.0, None))
    run(db.update_product(pid, name='New', price=3.5))
    p = run(db.get_product(pid))
    assert p['name'] == 'New' and float(p['price']) == 3.5
    run(db.delete_product(pid))
    p2 = run(db.get_product(pid))
    assert p2 is None


def test_update_no_fields_and_delete_nonexistent(tmp_path):
    db_path = tmp_path / 'adm3.db'
    run(init_db(str(db_path)))
    db = DB(str(db_path))
    cid = run(db.add_category('Z'))
    pid = run(db.add_product(cid, 'Tmp', 'd', 4.0, None))
    # update with no fields should not raise
    run(db.update_product(pid))
    # delete non-existent
    run(db.delete_product(99999))
    assert run(db.get_product(pid)) is not None
