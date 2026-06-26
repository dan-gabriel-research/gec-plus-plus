# embedder.py
# Converts text into numerical vectors (embeddings).
# Uses fastembed — lightweight, no PyTorch required, runs offline.
# Model: BAAI/bge-small-en-v1.5 (~23MB, downloads once, cached locally)

from fastembed import TextEmbedding
import numpy as np

MODEL_NAME = "BAAI/bge-small-en-v1.5"
_model = None


def _get_model() -> TextEmbedding:
    global _model
    if _model is None:
        print(f"  [Embedder] Loading model {MODEL_NAME}...")
        _model = TextEmbedding(model_name=MODEL_NAME)
        print(f"  [Embedder] Ready.")
    return _model


def embed(text: str) -> np.ndarray:
    """Convert a single string to a vector."""
    model = _get_model()
    vectors = list(model.embed([text]))
    v = np.array(vectors[0], dtype=np.float32)
    norm = np.linalg.norm(v)
    return v / norm if norm > 0 else v


def embed_batch(texts: list) -> np.ndarray:
    """Convert a list of strings to a matrix of vectors."""
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    model = _get_model()
    vectors = list(model.embed(texts))
    result = np.array(vectors, dtype=np.float32)
    if result.ndim == 1:
        result = result.reshape(1, -1)
    norms = np.linalg.norm(result, axis=1, keepdims=True)
    return result / np.where(norms > 0, norms, 1)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Similarity between two normalized vectors. 1.0 = identical, 0.0 = unrelated."""
    return float(np.dot(a, b))
