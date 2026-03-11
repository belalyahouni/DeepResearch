"""BGE embedding service — loads the model once and provides embed functions.

Uses BAAI/bge-base-en-v1.5 via sentence-transformers for nearest-neighbour search.
The model is loaded lazily on first call and cached for the process lifetime.
"""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

_MODEL_NAME = "BAAI/bge-base-en-v1.5"
# Applied to queries only — not to indexed documents (BGE retrieval convention)
_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    """Load and cache the BGE model. Uses MPS on Apple Silicon, else CPU."""
    import torch
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    return SentenceTransformer(_MODEL_NAME, device=device)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of document texts (no query prefix).

    Args:
        texts: List of text strings to embed (paper titles/abstracts).

    Returns:
        List of embedding vectors (each a list of floats, dimension 768).
    """
    model = _load_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def embed_query(text: str) -> list[float]:
    """Embed a single search query with the BGE query prefix.

    Applying the prefix at query time (not document indexing time) is the
    recommended usage for BGE retrieval models.

    Args:
        text: The search query to embed.

    Returns:
        Embedding vector (list of floats, dimension 768).
    """
    model = _load_model()
    embedding = model.encode([_QUERY_PREFIX + text], normalize_embeddings=True)
    return embedding[0].tolist()
