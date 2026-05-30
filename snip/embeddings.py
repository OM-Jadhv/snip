from pathlib import Path

import numpy as np
from fastembed import TextEmbedding

from snip.db import DATA_DIR

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CACHE_DIR = DATA_DIR / "model"

_model: TextEmbedding | None = None


def load_model() -> TextEmbedding:
    global _model
    if _model is None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _model = TextEmbedding(MODEL_NAME, cache_dir=str(CACHE_DIR))
    return _model


def encode(text: str) -> np.ndarray:
    model = load_model()
    return next(model.embed([text])).astype(np.float32)
