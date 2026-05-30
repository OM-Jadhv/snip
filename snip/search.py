import sqlite3

from snip.db import get_connection
from snip.embeddings import encode


def keyword_search(query: str, limit: int = 5) -> list[dict]:
    db = get_connection()
    pattern = f"%{query}%"
    rows = db.execute(
        "SELECT * FROM snips WHERE title LIKE ? OR body LIKE ? OR tags LIKE ? ORDER BY created_at DESC LIMIT ?",
        (pattern, pattern, pattern, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def vector_search(query: str, limit: int = 5) -> list[dict]:
    db = get_connection()
    embedding = encode(query)
    rows = db.execute(
        "SELECT id, distance FROM vec_snips WHERE embedding MATCH ? AND k = ?",
        (embedding, limit),
    ).fetchall()
    if not rows:
        return []

    ids = [r["id"] for r in rows]
    placeholders = ",".join("?" * len(ids))
    snip_rows = db.execute(
        f"SELECT * FROM snips WHERE id IN ({placeholders})", ids
    ).fetchall()
    snip_map = {r["id"]: dict(r) for r in snip_rows}

    results = []
    for r in rows:
        snip = snip_map.get(r["id"])
        if snip:
            snip["_distance"] = r["distance"]
            results.append(snip)
    return results


def hybrid_search(query: str, limit: int = 5) -> list[dict]:
    keyword_results = keyword_search(query, limit)
    vector_results = vector_search(query, limit)

    seen = set()
    merged = []

    for r in vector_results:
        seen.add(r["id"])
        merged.append(r)

    for r in keyword_results:
        if r["id"] not in seen:
            r["_distance"] = None
            merged.append(r)

    merged.sort(
        key=lambda x: (x["_distance"] if x["_distance"] is not None else float("inf"))
    )
    return merged[:limit]


def find_related(db: sqlite3.Connection, snip_id: int, limit: int = 3) -> list[dict]:
    row = db.execute("SELECT body FROM snips WHERE id = ?", (snip_id,)).fetchone()
    if not row:
        return []
    embedding = encode(row["body"])
    rows = db.execute(
        "SELECT id FROM vec_snips WHERE embedding MATCH ? AND k = ?",
        (embedding, limit + 1),
    ).fetchall()
    ids = [r["id"] for r in rows if r["id"] != snip_id][:limit]
    if not ids:
        return []
    placeholders = ",".join("?" * len(ids))
    snip_rows = db.execute(
        f"SELECT id, title, language, tags FROM snips WHERE id IN ({placeholders})", ids
    ).fetchall()
    return [dict(r) for r in snip_rows]
