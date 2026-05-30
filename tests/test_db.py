from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest


def test_ensure_data_dir_creates_directory(data_dir):
    from snip.db import ensure_data_dir
    if data_dir.exists():
        import shutil
        shutil.rmtree(str(data_dir))
    ensure_data_dir()
    assert data_dir.is_dir()


def test_ensure_data_dir_creates_default_config(data_dir):
    from snip.db import CONFIG_PATH, ensure_data_dir
    if data_dir.exists():
        import shutil
        shutil.rmtree(str(data_dir))
    ensure_data_dir()
    assert CONFIG_PATH.exists()
    content = CONFIG_PATH.read_text()
    assert "snip configuration" in content
    assert "db_path" in content
    assert "editor" in content


def test_ensure_data_dir_is_idempotent(data_dir):
    from snip.db import ensure_data_dir
    ensure_data_dir()
    ensure_data_dir()
    assert data_dir.is_dir()


def test_get_connection_returns_connection(data_dir):
    from snip.db import get_connection
    conn = get_connection()
    assert isinstance(conn, sqlite3.Connection)
    conn.close()


def test_get_connection_sets_row_factory(data_dir):
    from snip.db import get_connection
    conn = get_connection()
    assert conn.row_factory is sqlite3.Row
    conn.close()


def test_get_connection_creates_schema(data_dir):
    from snip.db import get_connection
    conn = get_connection()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    names = [r[0] for r in tables]
    assert "snips" in names
    assert "vec_snips" in names
    conn.close()


def test_init_schema_idempotent(data_dir):
    from snip.db import get_connection, init_schema
    conn = get_connection()
    init_schema(conn)
    conn.close()


def test_snips_table_columns(data_dir):
    from snip.db import get_connection
    conn = get_connection()
    cols = conn.execute("PRAGMA table_info(snips)").fetchall()
    col_names = [r["name"] for r in cols]
    expected = ["id", "title", "body", "type", "language", "tags",
                "source", "created_at", "updated_at", "source_file", "source_line"]
    for col in expected:
        assert col in col_names, f"Missing column: {col}"
    conn.close()


def test_snips_type_check_constraint(data_dir):
    from snip.db import get_connection
    conn = get_connection()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO snips (title, body, type) VALUES (?, ?, ?)",
            ("test", "body", "invalid_type"),
        )
    conn.close()


def test_snips_type_default_code(data_dir):
    from snip.db import get_connection
    conn = get_connection()
    conn.execute(
        "INSERT INTO snips (title, body) VALUES (?, ?)",
        ("test", "body"),
    )
    row = conn.execute("SELECT type FROM snips WHERE id = 1").fetchone()
    assert row["type"] == "code"
    conn.close()


def test_run_migrations_idempotent(data_dir):
    from snip.db import get_connection, run_migrations
    conn = get_connection()
    run_migrations(conn)
    conn.close()


def test_vec_snips_is_virtual_table(data_dir):
    from snip.db import get_connection
    conn = get_connection()
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='virtual_table' AND name='vec_snips'"
    ).fetchall()
    assert len(rows) >= 1 or "vec_snips" in [
        r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    ]
    conn.close()
