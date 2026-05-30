from __future__ import annotations

import json

import pytest
from snip.cli import app


def test_import_from_json(cli_runner, in_memory_db, mock_embed, tmp_path):
    src = tmp_path / "snips.json"
    src.write_text(json.dumps([
        {"title": "Imported1", "body": "body1"},
        {"title": "Imported2", "body": "body2", "language": "go"},
    ]))
    result = cli_runner.invoke(app, ["import", str(src)])
    assert result.exit_code == 0
    assert "Imported 2 snips" in result.output
    rows = in_memory_db.execute("SELECT * FROM snips").fetchall()
    assert len(rows) == 2


def test_import_from_directory(cli_runner, in_memory_db, mock_embed, tmp_path):
    (tmp_path / "hello.py").write_text("print('hello')")
    (tmp_path / "script.sh").write_text("echo hi")
    (tmp_path / "notes.md").write_text("# Notes")
    result = cli_runner.invoke(app, ["import", str(tmp_path)])
    assert result.exit_code == 0
    assert "Imported 3 snips" in result.output
    rows = in_memory_db.execute("SELECT * FROM snips").fetchall()
    assert len(rows) == 3


def test_import_dry_run_json(cli_runner, in_memory_db, mock_embed, tmp_path):
    src = tmp_path / "snips.json"
    src.write_text(json.dumps([
        {"title": "Dry1", "body": "body1"},
        {"title": "Dry2", "body": "body2"},
    ]))
    result = cli_runner.invoke(app, ["import", str(src), "--dry-run"])
    assert result.exit_code == 0
    assert "Would import 2 snips" in result.output
    rows = in_memory_db.execute("SELECT * FROM snips").fetchall()
    assert len(rows) == 0


def test_import_with_collection(cli_runner, in_memory_db, mock_embed, tmp_path):
    src = tmp_path / "snips.json"
    src.write_text(json.dumps([
        {"title": "Coll1", "body": "body1", "tags": "original"},
    ]))
    result = cli_runner.invoke(app, ["import", str(src), "--collection", "backup"])
    assert result.exit_code == 0
    row = in_memory_db.execute(
        "SELECT tags FROM snips WHERE title = ?", ("Coll1",)
    ).fetchone()
    assert row["tags"] == "original,backup"


def test_import_invalid_source(cli_runner):
    result = cli_runner.invoke(app, ["import", "/nonexistent/file.json"])
    assert result.exit_code != 0


def test_import_directory_skips_hidden_and_large(cli_runner, in_memory_db, mock_embed, tmp_path):
    (tmp_path / "visible.py").write_text("ok")
    (tmp_path / ".hidden.py").write_text("skip")
    result = cli_runner.invoke(app, ["import", str(tmp_path)])
    assert result.exit_code == 0
    rows = in_memory_db.execute("SELECT * FROM snips").fetchall()
    assert len(rows) == 1


def test_import_from_json_empty(cli_runner, in_memory_db, mock_embed, tmp_path):
    src = tmp_path / "empty.json"
    src.write_text("[]")
    result = cli_runner.invoke(app, ["import", str(src)])
    assert result.exit_code == 0
    assert "No snips to import" in result.output
