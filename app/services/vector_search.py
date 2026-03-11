"""ChromaDB vector search service — similarity search over the arXiv corpus.

Provides search_by_query (query-based) and find_related (paper-based) functions.
ChromaDB is initialised once with a persistent on-disk collection.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb

from app.services.embeddings import embed_query

_CHROMA_PATH = os.getenv("CHROMA_DB_PATH", str(Path(__file__).resolve().parent.parent.parent / "chroma_db"))
_COLLECTION_NAME = "arxiv_papers"


@lru_cache(maxsize=1)
def _get_collection() -> chromadb.Collection:
    """Get (or create) the ChromaDB collection. Cached for process lifetime."""
    client = chromadb.PersistentClient(path=_CHROMA_PATH)
    return client.get_or_create_collection(
        name=_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def search_by_query(
    query_text: str,
    *,
    n_results: int = 10,
) -> list[dict[str, Any]]:
    """Embed a query and find the most similar papers in the corpus.

    Args:
        query_text: The search query (already optimised by the classifier agent).
        n_results: Number of results to return.

    Returns:
        List of dicts with keys: arxiv_id, distance, similarity_score.
    """
    collection = _get_collection()
    query_embedding = embed_query(query_text)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["distances"],
    )

    hits: list[dict[str, Any]] = []
    if results["ids"] and results["ids"][0]:
        for arxiv_id, distance in zip(results["ids"][0], results["distances"][0]):
            hits.append({
                "arxiv_id": arxiv_id,
                "distance": distance,
                "similarity_score": round(1 - distance, 4),
            })
    return hits


def find_related(
    arxiv_id: str,
    *,
    n_results: int = 5,
) -> list[dict[str, Any]]:
    """Find papers similar to a given paper by looking up its embedding in ChromaDB.

    Args:
        arxiv_id: The arXiv ID of the source paper.
        n_results: Number of related papers to return (excluding the source).

    Returns:
        List of dicts with keys: arxiv_id, distance, similarity_score.

    Raises:
        ValueError: If the arxiv_id is not found in the collection.
    """
    collection = _get_collection()

    existing = collection.get(ids=[arxiv_id], include=["embeddings"])
    if not existing["ids"]:
        raise ValueError(f"Paper {arxiv_id} not found in vector store")

    paper_embedding = existing["embeddings"][0]

    results = collection.query(
        query_embeddings=[paper_embedding],
        n_results=n_results + 1,
        include=["distances"],
    )

    hits: list[dict[str, Any]] = []
    if results["ids"] and results["ids"][0]:
        for rid, distance in zip(results["ids"][0], results["distances"][0]):
            if rid != arxiv_id:
                hits.append({
                    "arxiv_id": rid,
                    "distance": distance,
                    "similarity_score": round(1 - distance, 4),
                })
    return hits[:n_results]
