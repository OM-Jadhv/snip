from __future__ import annotations

import pytest
from snip.cli import app


def test_delete_with_confirmation(cli_runner, in_memory_db, mock_embed, sample_snips,
                                   mock_confirm_yes):
    result = cli_runner.invoke(app, ["delete", str(sample_snips[0])])
    assert result.exit_code == 0
    assert "deleted" in result.output
    row = in_memory_db.execute(
        "SELECT id FROM snips WHERE id = ?", (sample_snips[0],)
    ).fetchone()
    assert row is None


def test_delete_without_confirmation(cli_runner, in_memory_db, mock_embed, sample_snips,
                                      mock_confirm_no):
    result = cli_runner.invoke(app, ["delete", str(sample_snips[0])])
    assert result.exit_code == 0
    assert "Cancelled" in result.output
    row = in_memory_db.execute(
        "SELECT id FROM snips WHERE id = ?", (sample_snips[0],)
    ).fetchone()
    assert row is not None


def test_delete_nonexistent(cli_runner):
    result = cli_runner.invoke(app, ["delete", "99999"])
    assert result.exit_code != 0
    assert "not found" in result.output
