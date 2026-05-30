from __future__ import annotations

from io import StringIO

import pytest
from rich.console import Console


@pytest.fixture
def test_console():
    return Console(file=StringIO(), width=120)


def test_show_table_empty(test_console, monkeypatch):
    from snip.display import show_table
    monkeypatch.setattr("snip.display.console", test_console)
    show_table([])
    output = test_console.file.getvalue()
    assert "No snips found" in output


def test_show_table_with_data(test_console, sample_snips, monkeypatch):
    from snip.display import show_table
    monkeypatch.setattr("snip.display.console", test_console)
    snips = [
        {"id": 1, "title": "Test", "language": "python",
         "tags": "a,b", "created_at": "2026-01-01"}
    ]
    show_table(snips)
    output = test_console.file.getvalue()
    assert "Test" in output
    assert "python" in output


def test_show_confirmation_true(monkeypatch):
    from snip.display import show_confirmation
    import rich.prompt
    monkeypatch.setattr(rich.prompt.Confirm, "ask", lambda *a, **kw: True)
    assert show_confirmation("Proceed?") is True


def test_show_confirmation_false(monkeypatch):
    from snip.display import show_confirmation
    import rich.prompt
    monkeypatch.setattr(rich.prompt.Confirm, "ask", lambda *a, **kw: False)
    assert show_confirmation("Proceed?") is False


def test_show_snip_basic(test_console, monkeypatch):
    from snip.display import show_snip
    monkeypatch.setattr("snip.display.console", test_console)
    monkeypatch.setattr("pyperclip.copy", lambda x: None)
    snip = {
        "id": 1, "title": "Hello", "body": "print('hello')",
        "type": "code", "language": "python", "tags": "demo",
        "source": None, "source_file": None, "source_line": None,
        "created_at": "2026-01-01", "updated_at": "2026-01-01",
    }
    show_snip(snip)
    output = test_console.file.getvalue()
    assert "Hello" in output
    assert "print" in output


def test_show_snip_with_source_file(test_console, tmp_path, monkeypatch):
    from snip.display import show_snip
    monkeypatch.setattr("snip.display.console", test_console)
    monkeypatch.setattr("pyperclip.copy", lambda x: None)
    src = tmp_path / "example.py"
    src.write_text("line1\nline2\nline3\nline4\nline5\n")
    snip = {
        "id": 1, "title": "File snip", "body": "body",
        "type": "code", "language": "python", "tags": None,
        "source": None, "source_file": str(src), "source_line": 3,
        "created_at": "2026-01-01", "updated_at": "2026-01-01",
    }
    show_snip(snip)
    output = test_console.file.getvalue()
    assert "Source:" in output
    assert "line3" in output


def test_show_snip_missing_source_file(test_console, monkeypatch):
    from snip.display import show_snip
    monkeypatch.setattr("snip.display.console", test_console)
    monkeypatch.setattr("pyperclip.copy", lambda x: None)
    snip = {
        "id": 1, "title": "Missing", "body": "body",
        "type": "code", "language": "python", "tags": None,
        "source": None, "source_file": "/nonexistent/path.py", "source_line": 5,
        "created_at": "2026-01-01", "updated_at": "2026-01-01",
    }
    show_snip(snip)
    output = test_console.file.getvalue()
    assert "no longer found" in output


def test_show_related_with_data(test_console, monkeypatch):
    from snip.display import show_related
    monkeypatch.setattr("snip.display.console", test_console)
    related = [
        {"id": 2, "title": "Related snip", "language": "python", "tags": "tag1"},
    ]
    show_related(related)
    output = test_console.file.getvalue()
    assert "Related snip" in output


def test_show_related_empty(test_console, monkeypatch):
    from snip.display import show_related
    monkeypatch.setattr("snip.display.console", test_console)
    show_related([])
    output = test_console.file.getvalue()
    assert output == ""


def test_show_stats(test_console, monkeypatch):
    from snip.display import show_stats
    monkeypatch.setattr("snip.display.console", test_console)
    stats = {
        "total": 10, "code_count": 7, "thought_count": 3,
        "earliest": "2026-01-01", "latest": "2026-06-01",
        "by_language": [{"language": "python", "count": 5}],
        "all_tags": ["a", "b", "a", "c"],
        "daily_counts": {"2026-05-30": 2},
    }
    show_stats(stats)
    output = test_console.file.getvalue()
    assert "10" in output
    assert "python" in output
    assert "Overview" in output
