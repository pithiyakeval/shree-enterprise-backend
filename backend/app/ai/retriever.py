# app/ai/retriever.py

import logging
import numpy as np
from typing import List, Dict

from app.ai.vectorestore import load_index
from app.ai.embeddings import embed_texts
from app.ai.utils import detect_language

logger = logging.getLogger("ai_retriever")

# ======================================================
# LOAD FAISS INDEX ONCE (SAFE)
# ======================================================

INDEX, METAS = load_index()

if INDEX is None or not METAS:
    logger.warning("⚠️ FAISS index not loaded. Retrieval disabled.")


# ======================================================
# RETRIEVER
# ======================================================

def retrieve(query: str, k: int = 4) -> List[Dict]:
    """
    Production-grade retriever.

    - Embeds query safely
    - Searches FAISS
    - Filters by language
    - Filters by similarity threshold
    - Returns clean context blocks
    """

    if not query or INDEX is None or not METAS:
        return []

    # ----------------------------
    # Detect language
    # ----------------------------
    language = detect_language(query)

    # ----------------------------
    # Embed query
    # ----------------------------
    vectors = embed_texts(query)
    if not vectors:
        logger.warning("Embedding failed for query")
        return []

    q_vec = np.array(vectors, dtype=np.float32)

    # ----------------------------
    # FAISS search
    # ----------------------------
    try:
        distances, indices = INDEX.search(q_vec, k * 3)
    except Exception as e:
        logger.exception("FAISS search failed")
        return []

    results: List[Dict] = []

    # ----------------------------
    # Filter results
    # ----------------------------
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0 or idx >= len(METAS):
            continue

        meta = METAS[idx]

        # Language filter (CRITICAL)
        if meta.get("language") != language:
            continue

        # Distance filter (VERY IMPORTANT)
        # Lower = more similar (L2 distance)
        if dist > 1.2:
            continue

        text = meta.get("text", "").strip()
        if not text or len(text) < 30:
            continue

        results.append({
            "text": text,
            "source": meta.get("source"),
            "distance": float(dist),
        })

        if len(results) >= k:
            break

    return results
