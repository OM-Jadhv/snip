from __future__ import annotations

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
    db.execute("DELETE FROM vec_snips WHERE id = ?", (snip_id,))
    db.execute(
        "INSERT INTO vec_snips(id, embedding) VALUES (?, ?)",
        (snip_id, embedding),
    )
    db.commit()


def delete_snip(snip_id: int) -> None:
    db = get_connection()
    db.execute("DELETE FROM snips WHERE id = ?", (snip_id,))
    db.execute("DELETE FROM vec_snips WHERE id = ?", (snip_id,))
    db.commit()


def bulk_add_snips(db, snips: list[dict], embed_fn) -> int:
    count = 0
    for s in snips:
        embedding = embed_fn(s["body"])
        cursor = db.execute(
            "INSERT INTO snips (title, body, type, language, tags, source, source_file, source_line) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (s["title"], s["body"], s.get("type", "code"), s.get("language"), s.get("tags"), s.get("source"), s.get("source_file"), s.get("source_line")),
        )
        db.execute(
            "INSERT INTO vec_snips(id, embedding) VALUES (?, ?)",
            (cursor.lastrowid, embedding),
        )
        count += 1
    db.commit()
    return count


def get_all_snips(db) -> list[dict]:
    rows = db.execute("SELECT * FROM snips ORDER BY created_at ASC").fetchall()
    return [dict(r) for r in rows]


def get_stats(db) -> dict:
    total = db.execute("SELECT COUNT(*) FROM snips").fetchone()[0]
    code_count = db.execute("SELECT COUNT(*) FROM snips WHERE type='code'").fetchone()[0]
    thought_count = db.execute("SELECT COUNT(*) FROM snips WHERE type='thought'").fetchone()[0]

    row = db.execute("SELECT MIN(created_at), MAX(created_at) FROM snips").fetchone()
    earliest = row[0] or ""
    latest = row[1] or ""

    lang_rows = db.execute(
        "SELECT COALESCE(language, 'text') AS language, COUNT(*) AS cnt FROM snips GROUP BY language ORDER BY cnt DESC"
    ).fetchall()
    by_language = [{"language": r["language"], "count": r["cnt"]} for r in lang_rows]

    tag_rows = db.execute("SELECT tags FROM snips WHERE tags IS NOT NULL AND tags != ''").fetchall()
    all_tags = []
    for r in tag_rows:
        for t in r["tags"].split(","):
            t = t.strip()
            if t:
                all_tags.append(t)

    from datetime import datetime, timedelta
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    daily_rows = db.execute(
        "SELECT DATE(created_at) AS d, COUNT(*) AS cnt FROM snips WHERE created_at >= ? GROUP BY d",
        (seven_days_ago,),
    ).fetchall()
    daily_counts = {r["d"]: r["cnt"] for r in daily_rows}

    return {
        "total": total,
        "code_count": code_count,
        "thought_count": thought_count,
        "earliest": earliest,
        "latest": latest,
        "by_language": by_language,
        "all_tags": all_tags,
        "daily_counts": daily_counts,
    }
