from __future__ import annotations

import pytest


def test_add_snip_returns_int(in_memory_db, mock_embed):
    from snip.store import add_snip
    sid = add_snip("Test", "body text", "code", language="python")
    assert isinstance(sid, int)
    assert sid >= 1


def test_add_snip_inserts_into_snips(in_memory_db, mock_embed):
    from snip.store import add_snip
    sid = add_snip("Test", "body text", "code", language="python")
    row = in_memory_db.execute("SELECT * FROM snips WHERE id = ?", (sid,)).fetchone()
    assert row["title"] == "Test"
    assert row["body"] == "body text"
    assert row["type"] == "code"
    assert row["language"] == "python"


def test_add_snip_inserts_embedding(in_memory_db, mock_embed):
    from snip.store import add_snip
    sid = add_snip("Test", "body text", "code")
    row = in_memory_db.execute(
        "SELECT id FROM vec_snips WHERE id = ?", (sid,)
    ).fetchone()
    assert row is not None
    assert row["id"] == sid


def test_add_snip_with_all_fields(in_memory_db, mock_embed):
    from snip.store import add_snip
    sid = add_snip(
        "Full", "body", "thought",
        language="text", tags="a,b,c", source="https://example.com",
        source_file="/path/to/file", source_line=42,
    )
    row = in_memory_db.execute("SELECT * FROM snips WHERE id = ?", (sid,)).fetchone()
    assert row["language"] == "text"
    assert row["tags"] == "a,b,c"
    assert row["source"] == "https://example.com"
    assert row["source_file"] == "/path/to/file"
    assert row["source_line"] == 42


def test_add_snip_minimal(in_memory_db, mock_embed):
    from snip.store import add_snip
    sid = add_snip("Minimal", "just body", "code")
    row = in_memory_db.execute("SELECT * FROM snips WHERE id = ?", (sid,)).fetchone()
    assert row["title"] == "Minimal"
    assert row["body"] == "just body"
    assert row["type"] == "code"
    assert row["language"] is None
    assert row["tags"] is None
    assert row["source"] is None


def test_get_snip_returns_dict(in_memory_db, mock_embed):
    from snip.store import add_snip, get_snip
    sid = add_snip("Get test", "body", "code")
    snip = get_snip(sid)
    assert isinstance(snip, dict)
    assert snip["id"] == sid
    assert snip["title"] == "Get test"


def test_get_snip_missing(in_memory_db):
    from snip.store import get_snip
    assert get_snip(99999) is None


def test_list_snips_returns_all(in_memory_db, mock_embed, sample_snips):
    from snip.store import list_snips
    results = list_snips()
    assert len(results) >= 5
    assert all(isinstance(r, dict) for r in results)


def test_list_snips_sorted_by_date_desc(in_memory_db, mock_embed, sample_snips):
    from snip.store import list_snips
    results = list_snips()
    dates = [r["created_at"] for r in results]
    assert dates == sorted(dates, reverse=True)


def test_list_snips_filter_by_tag(in_memory_db, mock_embed, sample_snips):
    from snip.store import list_snips
    results = list_snips(tag="list")
    assert len(results) >= 1
    assert all("list" in (r.get("tags") or "") for r in results)


def test_list_snips_filter_by_type(in_memory_db, mock_embed, sample_snips):
    from snip.store import list_snips
    results = list_snips(type="thought")
    assert len(results) >= 1
    assert all(r["type"] == "thought" for r in results)


def test_list_snips_filter_combined(in_memory_db, mock_embed, sample_snips):
    from snip.store import list_snips
    results = list_snips(tag="loop", type="code")
    assert len(results) >= 1
    assert all(r["type"] == "code" for r in results)


def test_list_snips_respects_limit(in_memory_db, mock_embed, sample_snips):
    from snip.store import list_snips
    results = list_snips(limit=2)
    assert len(results) <= 2


def test_list_snips_no_match(in_memory_db, mock_embed, sample_snips):
    from snip.store import list_snips
    results = list_snips(tag="nonexistent_tag_xyz")
    assert results == []


def test_update_snip_changes_body(in_memory_db, mock_embed, sample_snips):
    from snip.store import update_snip, get_snip
    original = get_snip(sample_snips[0])
    update_snip(sample_snips[0], "new body content")
    updated = get_snip(sample_snips[0])
    assert updated["body"] == "new body content"


def test_update_snip_reembeds(in_memory_db, mock_embed, sample_snips):
    from snip.store import update_snip, get_snip
    original = get_snip(sample_snips[0])
    update_snip(sample_snips[0], "new body content")
    vec_row = in_memory_db.execute(
        "SELECT id FROM vec_snips WHERE id = ?", (sample_snips[0],)
    ).fetchone()
    assert vec_row is not None


def test_update_snip_preserves_source_fields(in_memory_db, mock_embed, sample_snips):
    from snip.store import update_snip, get_snip
    update_snip(sample_snips[0], "updated body",
                source_file="/new/path", source_line=10)
    snip = get_snip(sample_snips[0])
    assert snip["source_file"] == "/new/path"
    assert snip["source_line"] == 10


def test_delete_snip_removes_from_both_tables(in_memory_db, mock_embed, sample_snips):
    from snip.store import delete_snip
    delete_snip(sample_snips[0])
    row = in_memory_db.execute(
        "SELECT id FROM snips WHERE id = ?", (sample_snips[0],)
    ).fetchone()
    assert row is None
    vec = in_memory_db.execute(
        "SELECT id FROM vec_snips WHERE id = ?", (sample_snips[0],)
    ).fetchone()
    assert vec is None


def test_delete_snip_nonexistent(in_memory_db):
    from snip.store import delete_snip
    delete_snip(99999)


def test_bulk_add_snips(in_memory_db, mock_embed):
    from snip.store import bulk_add_snips
    snips = [
        {"title": "Bulk1", "body": "body1"},
        {"title": "Bulk2", "body": "body2", "language": "go"},
    ]
    count = bulk_add_snips(in_memory_db, snips, mock_embed)
    assert count == 2
    rows = in_memory_db.execute("SELECT * FROM snips").fetchall()
    assert len(rows) == 2


def test_get_all_snips_returns_all(in_memory_db, mock_embed, sample_snips):
    from snip.store import get_all_snips
    results = get_all_snips(in_memory_db)
    assert len(results) >= 5


def test_get_all_snips_sorted_asc(in_memory_db, mock_embed, sample_snips):
    from snip.store import get_all_snips
    results = get_all_snips(in_memory_db)
    ids = [r["id"] for r in results]
    assert ids == sorted(ids)


def test_get_stats(in_memory_db, mock_embed, sample_snips):
    from snip.store import get_stats
    stats = get_stats(in_memory_db)
    assert stats["total"] >= 5
    assert stats["code_count"] >= 4
    assert stats["thought_count"] >= 1
    assert stats["earliest"]
    assert stats["latest"]
    assert isinstance(stats["by_language"], list)
    assert isinstance(stats["all_tags"], list)
    assert isinstance(stats["daily_counts"], dict)


def test_get_stats_empty(in_memory_db):
    from snip.store import get_stats
    stats = get_stats(in_memory_db)
    assert stats["total"] == 0
    assert stats["code_count"] == 0
    assert stats["thought_count"] == 0
