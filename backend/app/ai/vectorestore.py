# app/ai/vectorestore.py

import faiss
import numpy as np
import json
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Optional

logger = logging.getLogger("ai_vectorestore")

# ======================================================
# PATH CONFIG (ABSOLUTE, DOCKER-SAFE)
# ======================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

FAISS_PATH = DATA_DIR / "faiss.index"
META_PATH = DATA_DIR / "faiss_meta.json"


# ======================================================
# SAVE FAISS INDEX + METADATA
# ======================================================


def save_index(index: faiss.Index, metas: List[Dict]) -> None:
    """
    Persist FAISS index and metadata safely.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        faiss.write_index(index, str(FAISS_PATH))
        META_PATH.write_text(
            json.dumps(metas, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        logger.info("FAISS index saved successfully")
        logger.info("FAISS metadata saved successfully")

    except Exception as e:
        logger.error(f"Failed to save FAISS index: {e}")
        raise


# ======================================================
# LOAD FAISS INDEX + METADATA
# ======================================================


def load_index() -> Tuple[Optional[faiss.Index], List[Dict]]:
    """
    Load FAISS index and metadata.
    Returns (None, []) if not available.
    Never crashes backend.
    """

    if not FAISS_PATH.exists() or not META_PATH.exists():
        logger.warning("FAISS index or metadata not found. RAG disabled.")
        return None, []

    try:
        index = faiss.read_index(str(FAISS_PATH))
        metas = json.loads(META_PATH.read_text(encoding="utf-8"))

        if not isinstance(metas, list):
            raise ValueError("Invalid metadata format")

        logger.info(f"FAISS index loaded with {len(metas)} documents")
        return index, metas

    except Exception as e:
        logger.error(f"Failed to load FAISS index: {e}")
        return None, []


# ======================================================
# BUILD FAISS INDEX (INGEST PIPELINE)
# ======================================================


def build_faiss(embeddings: np.ndarray, metas: List[Dict]) -> None:
    """
    Build and persist FAISS index.
    Uses Flat index for small data (fast & stable).
    """

    if embeddings is None or len(embeddings) == 0:
        raise RuntimeError("Cannot build FAISS index: embeddings empty")

    if len(embeddings) != len(metas):
        raise ValueError("Embeddings and metadata size mismatch")

    embeddings = embeddings.astype(np.float32)
    dim = embeddings.shape[1]

    logger.info(f"Building FAISS index (vectors={len(embeddings)}, dim={dim})")

    # ---- SAFE INDEX TYPE ----
    # FlatL2 is best for small/medium datasets (<10k)
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    save_index(index, metas)

    logger.info("FAISS index build completed")


# ======================================================
# LOW-LEVEL SEARCH (OPTIONAL HELPER)
# ======================================================


def search_vectors(
    index: faiss.Index, query_vector: np.ndarray, top_k: int = 4
) -> List[int]:
    """
    Low-level FAISS search helper.
    Returns list of matching indices.
    """

    if index is None:
        return []

    if query_vector.ndim == 1:
        query_vector = np.array([query_vector], dtype=np.float32)

    try:
        _, ids = index.search(query_vector, top_k)
        return [int(i) for i in ids[0] if i >= 0]
    except Exception:
        return []
