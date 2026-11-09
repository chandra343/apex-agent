"""Unit tests for Database Explorer & SQL Query Tool."""
import sqlite3
import pytest
from apex.tools.db_ops import query_database


@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_store.db"
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, price REAL);")
    cur.execute("INSERT INTO products (name, price) VALUES ('Keyboard Mechanical', 750000);")
    cur.execute("INSERT INTO products (name, price) VALUES ('Mouse Wireless', 350000);")
    conn.commit()
    conn.close()
    return str(db_file)


def test_schema_inspection(test_db):
    res = query_database(test_db)
    assert "Database Schema" in res
    assert "products" in res
    assert "name" in res
    assert "price" in res


def test_select_query(test_db):
    res = query_database(test_db, "SELECT * FROM products ORDER BY id ASC;")
    assert "Keyboard Mechanical" in res
    assert "Mouse Wireless" in res
    assert "750000" in res


def test_insert_query(test_db):
    res = query_database(test_db, "INSERT INTO products (name, price) VALUES ('Monitor 24 Inch', 1500000);")
    assert "Operasi SQL Berhasil" in res
    assert "rows affected" in res

    # Verify insertion
    check = query_database(test_db, "SELECT COUNT(*) FROM products;")
    assert "3" in check
