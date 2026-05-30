from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile
from pathlib import Path

import numpy as np
import pytest
import sqlite_vec
from typer.testing import CliRunner

from snip.cli import app


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def tmp_home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    return home


@pytest.fixture
def db_path(tmp_home):
    from snip.db import DB_PATH
    return DB_PATH


@pytest.fixture
def data_dir(tmp_home):
    from snip.db import DATA_DIR
    return DATA_DIR


@pytest.fixture
def in_memory_db(monkeypatch):
    conn = sqlite3.connect(":memory:")
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")

    from snip.db import init_schema
    init_schema(conn)

    class NoCloseConnection:
        def __init__(self, c):
            self._conn = c
        def __getattr__(self, name):
            return getattr(self._conn, name)
        def close(self):
            pass

    wrapped = NoCloseConnection(conn)

    def mock_get_connection():
        return wrapped

    monkeypatch.setattr("snip.db.get_connection", mock_get_connection)
    monkeypatch.setattr("snip.store.get_connection", mock_get_connection)
    monkeypatch.setattr("snip.search.get_connection", mock_get_connection)
    monkeypatch.setattr("snip.cli.get_connection", mock_get_connection)
    return wrapped


@pytest.fixture(autouse=True)
def mock_embed(monkeypatch):
    def fake_encode(text: str) -> np.ndarray:
        return np.zeros(384, dtype=np.float32)

    monkeypatch.setattr("snip.embeddings.encode", fake_encode)
    monkeypatch.setattr("snip.store.encode", fake_encode)
    monkeypatch.setattr("snip.search.encode", fake_encode)
    return fake_encode


@pytest.fixture
def sample_snips(in_memory_db):
    from snip.store import add_snip
    ids = []
    snip_data = [
        ("Flatten a list", "flat = [item for sub in nested for item in sub]", "code", "python", "list,comprehension"),
        ("Read file safely", "with open('file.txt') as f:\n    data = f.read()", "code", "python", "io,file"),
        ("Why 42?", "Deep Thought computed it after 7.5 million years.", "thought", None, None),
        ("Bash loop", "for f in *.txt; do echo $f; done", "code", "bash", "loop,shell"),
        ("Callback pattern", "def fetch(cb):\n    cb(result)", "code", "javascript", "async,callback"),
    ]
    for title, body, typ, lang, tags in snip_data:
        sid = add_snip(title, body, typ, language=lang, tags=tags)
        ids.append(sid)
    return ids


@pytest.fixture
def mock_confirm_yes(monkeypatch):
    monkeypatch.setattr("snip.display.show_confirmation", lambda msg: True)
    monkeypatch.setattr("snip.cli.show_confirmation", lambda msg: True)


@pytest.fixture
def mock_confirm_no(monkeypatch):
    monkeypatch.setattr("snip.display.show_confirmation", lambda msg: False)
    monkeypatch.setattr("snip.cli.show_confirmation", lambda msg: False)


@pytest.fixture
def mock_editor(monkeypatch):
    def fake_edit_body(initial: str = "") -> str:
        return "edited body content"
    monkeypatch.setattr("snip.cli._edit_body", fake_edit_body)
    return fake_edit_body


@pytest.fixture
def mock_pyperclip(monkeypatch):
    monkeypatch.setattr("pyperclip.copy", lambda text: None)


@pytest.fixture
def mock_fzf_not_installed(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda cmd, **kw: None if cmd == "fzf" else shutil.which(cmd))


@pytest.fixture
def mock_fzf_installed(monkeypatch):
    original_which = shutil.which

    def fake_which(cmd, **kw):
        if cmd == "fzf":
            return "/usr/bin/fzf"
        return original_which(cmd)

    monkeypatch.setattr("shutil.which", fake_which)


@pytest.fixture
def mock_fzf_select(monkeypatch):
    class FakePopen:
        def __init__(self, *args, **kwargs):
            self.stdout = None
            self.stderr = None
            self.returncode = 0
            self.args = args
            self.kwargs = kwargs

        def communicate(self, input=None):
            return ("1|python|list,comprehension|Flatten a list\n", "")

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            pass

    monkeypatch.setattr("subprocess.Popen", FakePopen)
