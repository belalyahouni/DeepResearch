"""One-time ingest script — loads arXiv AI/ML papers into SQLite + ChromaDB.

Usage:
    python scripts/ingest_arxiv.py [--limit N]

Steps:
    1. Stream the arXiv CS papers dataset from HuggingFace
       (davanstrien/arxiv-cs-papers-classified)
    2. Filter to AI/ML categories: cs.AI, cs.LG, cs.CL, cs.CV, cs.NE, cs.MA, stat.ML
    3. Insert metadata into SQLite arxiv_papers table
    4. Embed abstracts with BAAI/bge-base-en-v1.5 in batches
    5. Upsert embeddings into ChromaDB

Requires:
    - Database already migrated: alembic upgrade head
    - HuggingFace datasets library: pip install datasets
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

import sqlalchemy
from datasets import load_dataset
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import DATABASE_URL
from app.models.arxiv_paper import ArxivPaper
from app.services.embeddings import embed_texts
from app.services.vector_search import _get_collection

AI_ML_CATEGORIES = {"cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.NE", "cs.MA", "stat.ML"}
EMBED_BATCH_SIZE = 64
DB_BATCH_SIZE = 1000

SYNC_DATABASE_URL = DATABASE_URL.replace("sqlite+aiosqlite", "sqlite")

HF_DATASET = "davanstrien/arxiv-cs-papers-classified"


def _is_ai_ml(categories_str: str) -> bool:
    """Check if any of the paper's categories match AI/ML."""
    cats = set(categories_str.split())
    return bool(cats & AI_ML_CATEGORIES)


def ingest(limit: int | None = None) -> None:
    """Run the full ingest pipeline."""
    engine = create_engine(SYNC_DATABASE_URL, echo=False)
    collection = _get_collection()

    print(f"Loading arXiv CS dataset from HuggingFace ({HF_DATASET})...")
    ds = load_dataset(HF_DATASET, split="train", streaming=True)

    # --- Pass 1: Filter and insert into SQLite ---
    print("[1/2] Filtering to AI/ML categories and inserting into SQLite...")
    papers_buffer: list[dict] = []
    total_read = 0
    total_kept = 0

    for record in ds:
        total_read += 1
        if total_read % 100_000 == 0:
            print(f"  ... read {total_read:,} papers, kept {total_kept:,}")

        categories = record.get("categories", "") or ""
        if not _is_ai_ml(categories):
            continue

        total_kept += 1

        arxiv_id = (record.get("id") or "").strip()
        if not arxiv_id:
            continue

        title = (record.get("title") or "").replace("\n", " ").strip()
        authors = (record.get("authors") or "").replace("\n", " ").strip()
        abstract = (record.get("abstract") or "").replace("\n", " ").strip() or None
        doi = record.get("doi") or None
        dt = record.get("update_date")
        year = dt.year if dt else None
        url = f"https://arxiv.org/abs/{arxiv_id}"

        papers_buffer.append({
            "arxiv_id": arxiv_id,
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "categories": categories,
            "year": year,
            "doi": doi,
            "url": url,
        })

        if len(papers_buffer) >= DB_BATCH_SIZE:
            with Session(engine) as session:
                session.execute(
                    sqlalchemy.insert(ArxivPaper).prefix_with("OR IGNORE"),
                    papers_buffer,
                )
                session.commit()
            papers_buffer = []

        if limit and total_kept >= limit:
            break

    if papers_buffer:
        with Session(engine) as session:
            session.execute(
                sqlalchemy.insert(ArxivPaper).prefix_with("OR IGNORE"),
                papers_buffer,
            )
            session.commit()

    print(f"  Done. {total_kept:,} AI/ML papers inserted into SQLite.")

    # --- Pass 2: Embed and upsert into ChromaDB ---
    print("[2/2] Embedding abstracts with bge-base-en-v1.5 and upserting into ChromaDB...")
    with Session(engine) as session:
        all_papers = session.query(ArxivPaper).all()

    batch_ids: list[str] = []
    batch_texts: list[str] = []
    embedded_count = 0
    start_time = time.time()

    for paper in all_papers:
        text = f"{paper.title} {paper.abstract}" if paper.abstract else paper.title
        batch_ids.append(paper.arxiv_id)
        batch_texts.append(text)

        if len(batch_ids) >= EMBED_BATCH_SIZE:
            embeddings = embed_texts(batch_texts)
            collection.upsert(ids=batch_ids, embeddings=embeddings)
            embedded_count += len(batch_ids)
            if embedded_count % 1000 == 0:
                elapsed = time.time() - start_time
                rate = embedded_count / elapsed if elapsed > 0 else 0
                print(f"  ... embedded {embedded_count:,} papers ({rate:.0f}/s)")
            batch_ids = []
            batch_texts = []

    if batch_ids:
        embeddings = embed_texts(batch_texts)
        collection.upsert(ids=batch_ids, embeddings=embeddings)
        embedded_count += len(batch_ids)

    elapsed = time.time() - start_time
    print(f"  Done. {embedded_count:,} embeddings stored in ChromaDB ({elapsed:.1f}s).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest arXiv AI/ML papers into SQLite + ChromaDB")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of AI/ML papers to ingest (default: all)",
    )
    args = parser.parse_args()
    ingest(limit=args.limit)
