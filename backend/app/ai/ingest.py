"""
Production RAG ingestion pipeline for Shree Enterprise AI assistant.

Features:
- Multilingual document ingestion
- Semantic chunking
- Embedding generation
- Qdrant vector storage
- Metadata payload support
- Batch ingestion for performance
"""

from pathlib import Path
import logging
from typing import List, Dict

from app.ai.embeddings import embed_texts
from app.ai.qdrant_store import init_collection, upsert_vectors

# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(levelname)s → %(message)s")
logger = logging.getLogger("ai_ingest")

# --------------------------------------------------
# Path configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

LANGUAGES = ["en", "gu"]

FILES = [
    "about.txt",
    "solar_short.txt",
    "solar_detailed.txt",
    "solar_pricing.txt",
    "mandap_short.txt",
    "mandap_detailed.txt",
    "mandap_pricing.txt",
    "faq.txt",
    "contact.txt",
]

# --------------------------------------------------
# Chunking logic
# --------------------------------------------------

def chunk_text(text: str) -> List[str]:
    """
    Convert raw document text into semantic chunks.
    """

    if not text:
        return []

    text = "\n".join(line.strip() for line in text.splitlines())

    chunks: List[str] = []

    for block in text.split("\n\n"):

        block = block.strip()

        if len(block) < 50:
            continue

        # Prevent large context chunks
        if len(block) > 800:

            for i in range(0, len(block), 600):

                sub = block[i : i + 600].strip()

                if len(sub) >= 50:
                    chunks.append(sub)

        else:
            chunks.append(block)

    return chunks


# --------------------------------------------------
# Load documents
# --------------------------------------------------

def load_documents():

    all_chunks: List[str] = []
    metas: List[Dict] = []

    for lang in LANGUAGES:

        lang_dir = DATA_DIR / lang

        if not lang_dir.exists():
            logger.warning(f"Missing language folder: {lang}")
            continue

        logger.info(f"Processing language: {lang}")

        for file_name in FILES:

            file_path = lang_dir / file_name

            if not file_path.exists():
                logger.warning(f"Missing file: {lang}/{file_name}")
                continue

            try:
                text = file_path.read_text(encoding="utf-8").strip()
            except Exception as e:
                logger.error(f"Failed reading {file_path}: {e}")
                continue

            chunks = chunk_text(text)

            if not chunks:
                continue

            for idx, chunk in enumerate(chunks):

                metas.append(
                    {
                        "language": lang,
                        "source": file_name.replace(".txt", ""),
                        "chunk_id": idx,
                        "text": chunk,
                    }
                )

                all_chunks.append(chunk)

            logger.info(f"{file_name} → {len(chunks)} chunks")

    return all_chunks, metas


# --------------------------------------------------
# Batch embedding
# --------------------------------------------------

def embed_chunks(chunks: List[str]):

    logger.info("Generating embeddings")

    embeddings = embed_texts(chunks)

    if not embeddings:
        raise RuntimeError("Embedding generation failed")

    logger.info(f"Embeddings created: {len(embeddings)}")

    return embeddings


# --------------------------------------------------
# Batch upsert to Qdrant
# --------------------------------------------------

def store_vectors(vectors, metas):

    logger.info("Initializing Qdrant collection")

    init_collection()

    payloads = []

    for meta in metas:

        payloads.append(
            {
                "text": meta["text"],
                "source": meta["source"],
                "language": meta["language"],
                "chunk_id": meta["chunk_id"],
            }
        )
    init_collection()
    
    upsert_vectors(vectors, payloads)

    logger.info("Vectors stored in Qdrant")


# --------------------------------------------------
# Main ingestion pipeline
# --------------------------------------------------

def run():

    logger.info("Starting ingestion pipeline")

    chunks, metas = load_documents()

    if not chunks:
        raise RuntimeError("No document chunks found")

    logger.info(f"Total chunks prepared: {len(chunks)}")

    vectors = embed_chunks(chunks)

    store_vectors(vectors, metas)

    logger.info("Ingestion completed successfully")


# --------------------------------------------------
# CLI entry
# --------------------------------------------------

if __name__ == "__main__":
    run()