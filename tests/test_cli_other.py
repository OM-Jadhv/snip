from __future__ import annotations

import pytest
from snip.cli import app


class TestList:
    def test_list_shows_snips(self, cli_runner, in_memory_db, mock_embed, sample_snips):
        result = cli_runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "Flatten a list" in result.output

    def test_list_filter_by_tag(self, cli_runner, in_memory_db, mock_embed, sample_snips):
        result = cli_runner.invoke(app, ["list", "--tag", "list"])
        assert result.exit_code == 0
        assert "Flatten" in result.output

    def test_list_filter_by_type(self, cli_runner, in_memory_db, mock_embed, sample_snips):
        result = cli_runner.invoke(app, ["list", "--type", "thought"])
        assert result.exit_code == 0
        assert "Why 42?" in result.output

    def test_list_respects_limit(self, cli_runner, in_memory_db, mock_embed, sample_snips):
        result = cli_runner.invoke(app, ["list", "--limit", "1"])
        assert result.exit_code == 0


class TestStats:
    def test_stats_output(self, cli_runner, in_memory_db, mock_embed, sample_snips):
        result = cli_runner.invoke(app, ["stats"])
        assert result.exit_code == 0
        assert "Overview" in result.output
        assert str(len(sample_snips)) in result.output

    def test_stats_empty(self, cli_runner, in_memory_db, mock_embed):
        result = cli_runner.invoke(app, ["stats"])
        assert result.exit_code == 0
        assert "0" in result.output


class TestCheck:
    def test_check_all_exist(self, cli_runner, in_memory_db, mock_embed, tmp_path):
        from snip.store import add_snip
        src = tmp_path / "exists.py"
        src.write_text("ok")
        add_snip("Check test", "body", "code", source_file=str(src), source_line=1)
        result = cli_runner.invoke(app, ["check"])
        assert result.exit_code == 0
        assert "found" in result.output

    def test_check_missing_reported(self, cli_runner, in_memory_db, mock_embed):
        from snip.store import add_snip
        add_snip("Check missing", "body", "code",
                 source_file="/nonexistent/file.py", source_line=1)
        result = cli_runner.invoke(app, ["check"])
        assert result.exit_code == 0
        assert "missing" in result.output

    def test_check_no_linked(self, cli_runner, in_memory_db, mock_embed, sample_snips):
        result = cli_runner.invoke(app, ["check"])
        assert result.exit_code == 0
        assert "No linked snips" in result.output


class TestUse:
    def test_use_no_fzf(self, cli_runner, mock_fzf_not_installed):
        result = cli_runner.invoke(app, ["use"])
        assert result.exit_code != 0
        assert "fzf is required" in result.output

    def test_use_with_fzf(self, cli_runner, in_memory_db, mock_embed, sample_snips,
                           mock_fzf_installed, mock_fzf_select):
        result = cli_runner.invoke(app, ["use"])
        assert result.exit_code == 0
        assert "Copied snip 1" in result.output or "Flatten" in result.output

    def test_use_no_snips(self, cli_runner, in_memory_db, mock_embed,
                           mock_fzf_installed):
        result = cli_runner.invoke(app, ["use"])
        assert result.exit_code == 0
        assert "No snips" in result.output


class TestReindex:
    def test_reindex(self, cli_runner, in_memory_db, mock_embed, sample_snips):
        result = cli_runner.invoke(app, ["reindex"])
        assert result.exit_code == 0
        assert "Re-indexed" in result.output
        assert str(len(sample_snips)) in result.output

    def test_reindex_empty(self, cli_runner, in_memory_db, mock_embed):
        result = cli_runner.invoke(app, ["reindex"])
        assert result.exit_code == 0
        assert "Re-indexed 0" in result.output


class TestInit:
    def test_init(self, cli_runner, monkeypatch):
        monkeypatch.setattr("snip.embeddings.load_model", lambda: None)
        result = cli_runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert "Model ready" in result.output
