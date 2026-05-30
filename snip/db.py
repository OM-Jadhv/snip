import sqlite3
from pathlib import Path

import sqlite_vec

DATA_DIR = Path.home() / ".snip"
DB_PATH = DATA_DIR / "snip.db"
CONFIG_PATH = DATA_DIR / "config.toml"


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(
            "# snip configuration\n"
            '# db_path = "~/.snip/snip.db"\n'
            '# editor = "vim"\n'
        )


def get_connection() -> sqlite3.Connection:
    ensure_data_dir()
    db = sqlite3.connect(str(DB_PATH))
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA synchronous = NORMAL")
    db.execute("PRAGMA cache_size = -64000")
    init_schema(db)
    return db


def run_migrations(db: sqlite3.Connection) -> None:
    for col, coltype in [("source_file", "TEXT"), ("source_line", "INTEGER")]:
        try:
            db.execute(f"ALTER TABLE snips ADD COLUMN {col} {coltype}")
        except sqlite3.OperationalError:
            pass
    db.commit()


def init_schema(db: sqlite3.Connection) -> None:
    db.executescript("""
        CREATE TABLE IF NOT EXISTS snips (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            body        TEXT NOT NULL,
            type        TEXT CHECK(type IN ('code', 'thought')) DEFAULT 'code',
            language    TEXT,
            tags        TEXT,
            source      TEXT,
            created_at  TEXT DEFAULT (datetime('now')),
            updated_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS vec_snips USING vec0(
            id          INTEGER PRIMARY KEY,
            embedding   FLOAT[384]
        );
    """)
    db.commit()
    run_migrations(db)
