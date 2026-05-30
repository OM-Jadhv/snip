from __future__ import annotations

import pytest
from snip.cli import app


def test_edit_saves_changes(cli_runner, in_memory_db, mock_embed, sample_snips,
                             mock_editor):
    result = cli_runner.invoke(app, ["edit", str(sample_snips[0])])
    assert result.exit_code == 0
    assert "updated" in result.output
    row = in_memory_db.execute(
        "SELECT body FROM snips WHERE id = ?", (sample_snips[0],)
    ).fetchone()
    assert row["body"] == "edited body content"


def test_edit_no_changes(cli_runner, in_memory_db, mock_embed, sample_snips,
                          monkeypatch):
    from snip.store import get_snip
    original = get_snip(sample_snips[0])

    def fake_edit_no_change(initial=""):
        return original["body"]

    monkeypatch.setattr("snip.cli._edit_body", fake_edit_no_change)
    result = cli_runner.invoke(app, ["edit", str(sample_snips[0])])
    assert result.exit_code == 0
    assert "No changes" in result.output


def test_edit_nonexistent(cli_runner):
    result = cli_runner.invoke(app, ["edit", "99999"])
    assert result.exit_code != 0
    assert "not found" in result.output
