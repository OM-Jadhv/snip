from snip.db import get_connection
from snip.embeddings import encode


def add_snip(title: str, body: str, type: str, language: str | None = None,
             tags: str | None = None, source: str | None = None,
             source_file: str | None = None, source_line: int | None = None) -> int:
    db = get_connection()
    cursor = db.execute(
        "INSERT INTO snips (title, body, type, language, tags, source, source_file, source_line) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (title, body, type, language, tags, source, source_file, source_line),
    )
    snip_id = cursor.lastrowid

    embedding = encode(body)
    db.execute(
        "INSERT INTO vec_snips(id, embedding) VALUES (?, ?)",
        (snip_id, embedding),
    )
    db.commit()
    return snip_id


def get_snip(snip_id: int) -> dict | None:
    db = get_connection()
    row = db.execute(
        "SELECT * FROM snips WHERE id = ?", (snip_id,)
    ).fetchone()
    return dict(row) if row else None


def list_snips(tag: str | None = None, type: str | None = None,
               limit: int = 20) -> list[dict]:
    db = get_connection()
    conditions = []
    params = []

    if tag:
        conditions.append("tags LIKE ?")
        params.append(f"%{tag}%")
    if type:
        conditions.append("type = ?")
        params.append(type)

    where = " AND ".join(conditions) if conditions else "1=1"
    rows = db.execute(
        f"SELECT * FROM snips WHERE {where} ORDER BY created_at DESC LIMIT ?",
        [*params, limit],
    ).fetchall()
    return [dict(r) for r in rows]


def update_snip(snip_id: int, body: str, source_file: str | None = None,
               source_line: int | None = None) -> None:
    db = get_connection()
    db.execute(
        "UPDATE snips SET body = ?, updated_at = datetime('now'), source_file = COALESCE(?, source_file), source_line = COALESCE(?, source_line) WHERE id = ?",
        (body, source_file, source_line, snip_id),
    )
    embedding = encode(body)
    db.execute(
        "INSERT OR REPLACE INTO vec_snips(id, embedding) VALUES (?, ?)",
        (snip_id, embedding),
    )
    db.commit()


def delete_snip(snip_id: int) -> None:
    db = get_connection()
    db.execute("DELETE FROM snips WHERE id = ?", (snip_id,))
    db.execute("DELETE FROM vec_snips WHERE id = ?", (snip_id,))
    db.commit()
