from __future__ import annotations

import pytest


def test_keyword_search_matches_title(in_memory_db, mock_embed, sample_snips):
    from snip.search import keyword_search
    results = keyword_search("Flatten")
    assert len(results) >= 1
    assert results[0]["title"] == "Flatten a list"


def test_keyword_search_matches_body(in_memory_db, mock_embed, sample_snips):
    from snip.search import keyword_search
    results = keyword_search("computed")
    assert len(results) >= 1


def test_keyword_search_matches_tags(in_memory_db, mock_embed, sample_snips):
    from snip.search import keyword_search
    results = keyword_search("comprehension")
    assert len(results) >= 1


def test_keyword_search_respects_limit(in_memory_db, mock_embed, sample_snips):
    from snip.search import keyword_search
    results = keyword_search("list", limit=1)
    assert len(results) <= 1


def test_keyword_search_no_match(in_memory_db, mock_embed, sample_snips):
    from snip.search import keyword_search
    results = keyword_search("xyznonexistent")
    assert results == []


def test_vector_search_returns_results(in_memory_db, mock_embed, sample_snips):
    from snip.search import vector_search
    results = vector_search("some query")
    assert len(results) >= 1
    assert all("_distance" in r for r in results)


def test_vector_search_returns_ranked(in_memory_db, mock_embed, sample_snips):
    from snip.search import vector_search
    results = vector_search("some query")
    distances = [r["_distance"] for r in results]
    assert distances == sorted(distances)


def test_vector_search_empty_db(in_memory_db, mock_embed):
    from snip.search import vector_search
    results = vector_search("anything")
    assert results == []


def test_hybrid_search_deduplicates(in_memory_db, mock_embed, sample_snips):
    from snip.search import hybrid_search
    results = hybrid_search("list")
    ids = [r["id"] for r in results]
    assert len(ids) == len(set(ids))


def test_hybrid_search_merges_correctly(in_memory_db, mock_embed, sample_snips):
    from snip.search import hybrid_search
    results = hybrid_search("list")
    assert len(results) >= 1


def test_hybrid_search_respects_limit(in_memory_db, mock_embed, sample_snips):
    from snip.search import hybrid_search
    results = hybrid_search("list", limit=1)
    assert len(results) <= 1


def test_hybrid_search_with_empty(in_memory_db, mock_embed):
    from snip.search import hybrid_search
    results = hybrid_search("anything")
    assert results == []


def test_find_related_excludes_self(in_memory_db, mock_embed, sample_snips):
    from snip.search import find_related
    related = find_related(in_memory_db, sample_snips[0])
    ids = [r["id"] for r in related]
    assert sample_snips[0] not in ids


def test_find_related_returns_up_to_limit(in_memory_db, mock_embed, sample_snips):
    from snip.search import find_related
    related = find_related(in_memory_db, sample_snips[0], limit=2)
    assert len(related) <= 2


def test_find_related_missing_snip(in_memory_db, mock_embed):
    from snip.search import find_related
    related = find_related(in_memory_db, 99999)
    assert related == []


def test_find_related_returns_dicts_with_keys(in_memory_db, mock_embed, sample_snips):
    from snip.search import find_related
    related = find_related(in_memory_db, sample_snips[0])
    if related:
        assert "id" in related[0]
        assert "title" in related[0]
        assert "language" in related[0]
        assert "tags" in related[0]
