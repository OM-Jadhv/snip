from __future__ import annotations

import json

import pytest
from snip.cli import app


def test_export_json_to_stdout(cli_runner, in_memory_db, mock_embed, sample_snips):
    result = cli_runner.invoke(app, ["export", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) >= 5


def test_export_markdown_to_stdout(cli_runner, in_memory_db, mock_embed, sample_snips):
    result = cli_runner.invoke(app, ["export", "--format", "markdown"])
    assert result.exit_code == 0
    assert "Snip Library Export" in result.output
    assert "Flatten a list" in result.output
    assert "```python" in result.output


def test_export_to_file(cli_runner, in_memory_db, mock_embed, sample_snips, tmp_path):
    out = tmp_path / "export.json"
    result = cli_runner.invoke(app, [
        "export", "--format", "json", "--output", str(out),
    ])
    assert result.exit_code == 0
    assert out.exists()
    data = json.loads(out.read_text())
    assert len(data) >= 5


def test_export_empty(cli_runner, in_memory_db, mock_embed):
    result = cli_runner.invoke(app, ["export", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data == []
