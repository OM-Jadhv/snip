from __future__ import annotations

import numpy as np
import pytest


def test_encode_returns_ndarray(mock_embed):
    result = mock_embed("hello world")
    assert isinstance(result, np.ndarray)
    assert result.dtype == np.float32


def test_encode_returns_384_dim(mock_embed):
    result = mock_embed("hello world")
    assert result.shape == (384,)


def test_encode_empty_string(mock_embed):
    result = mock_embed("")
    assert result.shape == (384,)


def test_encode_singleton(mock_embed):
    r1 = mock_embed("same text")
    r2 = mock_embed("same text")
    np.testing.assert_array_equal(r1, r2)


def test_load_model_returns_model(monkeypatch):
    import numpy as np
    fake_model = object()

    def fake_load_model():
        return fake_model

    monkeypatch.setattr("snip.embeddings.load_model", fake_load_model)
    model = fake_load_model()
    assert model is fake_model
