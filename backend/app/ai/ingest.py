# app/ai/ingest.py
"""
FAISS ingestion pipeline for Shree Enterprise AI assistant.

- Reads multilingual business documents
- Splits into clean semantic chunks
- Embeds using sentence-transformers
- Builds and persists FAISS index + metadata

SAFE FOR:
- Local development
- Docker
- Production server
"""

from pathlib import Path
import numpy as np
import logging

from app.ai.embeddings import embed_texts
from app.ai.vectorestore import build_faiss

# -------------------------------------------------
# Logging (production-safe)
# -------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s → %(message)s"
)
logger = logging.getLogger("ai_ingest")

# -------------------------------------------------
# Path configuration (ABSOLUTE, SAFE)
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent   # app/
DATA_DIR = BASE_DIR / "data"                        # app/data/

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

# -------------------------------------------------
# Chunking logic (clean, semantic)
# -------------------------------------------------
def chunk_text(text: str) -> list[str]:
    """
    Splits text into semantic chunks.
    Keeps content human-readable and answer-ready.
    """
    if not text:
        return []

    # Normalize whitespace
    text = "\n".join(line.strip() for line in text.splitlines())

    chunks: list[str] = []
    for block in text.split("\n\n"):
        block = block.strip()

        # Skip very small noise
        if len(block) < 50:
            continue

        # Hard safety cap (prevents prompt overload)
        if len(block) > 800:
            for i in range(0, len(block), 600):
                sub = block[i : i + 600].strip()
                if len(sub) >= 50:
                    chunks.append(sub)
        else:
            chunks.append(block)

    return chunks

# -------------------------------------------------
# Ingestion pipeline
# -------------------------------------------------
def run() -> None:
    logger.info("🚀 Starting AI ingestion pipeline")

    all_chunks: list[str] = []
    metas: list[dict] = []

    for lang in LANGUAGES:
        lang_dir = DATA_DIR / lang

        if not lang_dir.exists():
            logger.warning(f"⚠️ Language folder missing: {lang_dir}")
            continue

        logger.info(f"📂 Processing language: {lang}")

        for file_name in FILES:
            file_path = lang_dir / file_name

            if not file_path.exists():
                logger.warning(f"⚠️ Missing file: {lang}/{file_name}")
                continue

            try:
                text = file_path.read_text(encoding="utf-8").strip()
            except Exception as e:
                logger.error(f"❌ Failed reading {file_path}: {e}")
                continue

            chunks = chunk_text(text)

            if not chunks:
                logger.warning(f"⚠️ No valid chunks in {file_path.name}")
                continue

            for idx, chunk in enumerate(chunks):
                metas.append({
                    "language": lang,
                    "source": file_name.replace(".txt", ""),
                    "chunk_id": idx,
                    "text": chunk
                })
                all_chunks.append(chunk)

            logger.info(f"✅ {file_name}: {len(chunks)} chunks")

    # -------------------------------------------------
    # Final validation
    # -------------------------------------------------
    if not all_chunks:
        raise RuntimeError(
            "❌ Ingestion failed: No chunks found. "
            "Check app/data files."
        )

    logger.info(f"🔹 Total chunks prepared: {len(all_chunks)}")

    # -------------------------------------------------
    # Embedding + FAISS build
    # -------------------------------------------------
    try:
        embeddings = np.array(
            embed_texts(all_chunks),
            dtype=np.float32
        )
    except Exception as e:
        raise RuntimeError(f"❌ Embedding failed: {e}")

    build_faiss(embeddings, metas)

    logger.info("✅ FAISS index built successfully")
    logger.info("🎉 Multilingual ingestion complete")

# -------------------------------------------------
# CLI entry
# -------------------------------------------------
if __name__ == "__main__":
    run()
