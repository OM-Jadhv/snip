from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from snip.db import DATA_DIR

MODEL_NAME = "all-MiniLM-L6-v2"
CACHE_DIR = DATA_DIR / "model"

_model: SentenceTransformer | None = None


def load_model() -> SentenceTransformer:
    global _model
    if _model is None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _model = SentenceTransformer(MODEL_NAME, cache_folder=str(CACHE_DIR))
    return _model


def encode(text: str) -> np.ndarray:
    model = load_model()
    return model.encode(text).astype(np.float32)
