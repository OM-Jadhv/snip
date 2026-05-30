from __future__ import annotations

import pytest
from snip.cli import app


def test_find_returns_results(cli_runner, in_memory_db, mock_embed, sample_snips):
    result = cli_runner.invoke(app, ["find", "list"])
    assert result.exit_code == 0
    assert "Flatten" in result.output


def test_find_text_only(cli_runner, in_memory_db, mock_embed, sample_snips):
    result = cli_runner.invoke(app, ["find", "list", "--text-only"])
    assert result.exit_code == 0
    assert "Flatten" in result.output


def test_find_no_results(cli_runner, in_memory_db, mock_embed):
    result = cli_runner.invoke(app, ["find", "anything"])
    assert result.exit_code == 0
    assert "No matches found" in result.output


def test_find_respects_limit(cli_runner, in_memory_db, mock_embed, sample_snips):
    result = cli_runner.invoke(app, ["find", "for", "--limit", "1"])
    assert result.exit_code == 0
    table_lines = [l for l in result.output.split("\n") if l.strip() and not l.startswith("─") and "ID" not in l and "Title" not in l]
    counts = sum(1 for l in table_lines if l.strip().startswith((" ", "")) and any(c.isdigit() for c in l[:5]))
    assert counts <= 1 or "No matches" in result.output


def test_find_empty_db(cli_runner, in_memory_db, mock_embed):
    result = cli_runner.invoke(app, ["find", "anything"])
    assert result.exit_code == 0
    assert "No matches found" in result.output
