from __future__ import annotations

import pytest
from snip.cli import app


def test_get_shows_snip(cli_runner, in_memory_db, mock_embed, sample_snips,
                         mock_pyperclip):
    result = cli_runner.invoke(app, ["get", str(sample_snips[0])])
    assert result.exit_code == 0
    assert "Flatten a list" in result.output
    assert "flat =" in result.output


def test_get_nonexistent(cli_runner):
    result = cli_runner.invoke(app, ["get", "99999"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_get_no_vector(cli_runner, in_memory_db, mock_embed, sample_snips,
                        mock_pyperclip):
    result = cli_runner.invoke(app, ["get", str(sample_snips[0]), "--no-vector"])
    assert result.exit_code == 0
    assert "Flatten a list" in result.output


def test_get_with_source_file(cli_runner, in_memory_db, mock_embed, tmp_path,
                               mock_pyperclip):
    from snip.store import add_snip
    src = tmp_path / "example.py"
    src.write_text("line1\nline2\ndef foo():\n    pass\n")
    sid = add_snip("Source snip", "body", "code", source_file=str(src), source_line=3)
    result = cli_runner.invoke(app, ["get", str(sid)])
    assert result.exit_code == 0
    assert "Source:" in result.output
