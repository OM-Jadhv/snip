from __future__ import annotations

import pytest
from snip.cli import app


def test_add_basic(cli_runner, in_memory_db, mock_embed):
    result = cli_runner.invoke(app, ["add", "Test snip", "--body", "hello world"])
    assert result.exit_code == 0
    assert "Snip" in result.output
    assert "saved" in result.output
    row = in_memory_db.execute(
        "SELECT * FROM snips WHERE title = ?", ("Test snip",)
    ).fetchone()
    assert row is not None
    assert row["body"] == "hello world"


def test_add_with_all_flags(cli_runner, in_memory_db, mock_embed):
    result = cli_runner.invoke(app, [
        "add", "Full snip",
        "--body", "some code",
        "--lang", "rust",
        "--tags", "test,demo",
        "--type", "code",
        "--source", "https://example.com",
        "--file", "/tmp/test.rs",
        "--line", "10",
    ])
    assert result.exit_code == 0
    row = in_memory_db.execute(
        "SELECT * FROM snips WHERE title = ?", ("Full snip",)
    ).fetchone()
    assert row["language"] == "rust"
    assert row["tags"] == "test,demo"
    assert row["type"] == "code"
    assert row["source"] == "https://example.com"


def test_add_from_file(cli_runner, in_memory_db, mock_embed, tmp_path):
    src = tmp_path / "snippet.py"
    src.write_text("def foo(): pass")
    result = cli_runner.invoke(app, [
        "add", "From file",
        "--from-file", str(src),
    ])
    assert result.exit_code == 0
    row = in_memory_db.execute(
        "SELECT * FROM snips WHERE title = ?", ("From file",)
    ).fetchone()
    assert row["body"] == "def foo(): pass"
    assert row["source_file"] == str(src.resolve())
    assert row["source_line"] == 1


def test_add_body_and_from_file_conflict(cli_runner):
    result = cli_runner.invoke(app, [
        "add", "Conflict",
        "--body", "hello",
        "--from-file", "/tmp/x.py",
    ])
    assert result.exit_code != 0
    assert "Cannot use --body and --from-file together" in result.output


def test_add_line_without_file(cli_runner):
    result = cli_runner.invoke(app, [
        "add", "Bad", "--body", "x", "--line", "5",
    ])
    assert result.exit_code != 0
    assert "--line requires --file" in result.output


def test_add_type_auto_code_when_lang(cli_runner, in_memory_db, mock_embed):
    result = cli_runner.invoke(app, [
        "add", "Auto code", "--body", "fn main()", "--lang", "rust",
    ])
    assert result.exit_code == 0
    row = in_memory_db.execute(
        "SELECT * FROM snips WHERE title = ?", ("Auto code",)
    ).fetchone()
    assert row["type"] == "code"


def test_add_type_auto_thought_when_no_lang(cli_runner, in_memory_db, mock_embed):
    result = cli_runner.invoke(app, [
        "add", "Auto thought", "--body", "just thinking",
    ])
    assert result.exit_code == 0
    row = in_memory_db.execute(
        "SELECT * FROM snips WHERE title = ?", ("Auto thought",)
    ).fetchone()
    assert row["type"] == "thought"


def test_add_stdin_pipe(cli_runner, in_memory_db, mock_embed, monkeypatch):
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    result = cli_runner.invoke(app, [
        "add", "Piped input",
    ], input="piped body content")
    assert result.exit_code == 0
    row = in_memory_db.execute(
        "SELECT * FROM snips WHERE title = ?", ("Piped input",)
    ).fetchone()
    assert row["body"] == "piped body content"



