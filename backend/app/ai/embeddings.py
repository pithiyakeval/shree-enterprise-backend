# app/ai/embeddings.py

import os
import logging
import numpy as np
from typing import List, Union

from sentence_transformers import SentenceTransformer

logger = logging.getLogger("ai_embeddings")

# ======================================================
# CONFIG
# ======================================================

EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2"
)

HF_CACHE_DIR = "/ai-models/hf-cache"

# ======================================================
# LOAD MODEL ONCE (SAFE SINGLETON)
# ======================================================

_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    """
    Load SentenceTransformer once.
    Never crashes the app — raises RuntimeError only at startup/ingest.
    """
    global _model

    if _model is not None:
        return _model

    try:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")

        _model = SentenceTransformer(
            EMBEDDING_MODEL_NAME,
            cache_folder=HF_CACHE_DIR,
            local_files_only=True
        )

        logger.info("Embedding model loaded successfully")
        return _model

    except Exception as e:
        logger.exception("❌ Failed to load embedding model")
        raise RuntimeError(
            f"Embedding model load failed: {EMBEDDING_MODEL_NAME}"
        ) from e


# ======================================================
# EMBEDDING FUNCTION (SAFE)
# ======================================================

def embed_texts(
    texts: Union[str, List[str]]
) -> List[np.ndarray]:
    """
    Convert text(s) into float32 embeddings.
    Always returns a list of numpy arrays.
    """

    if not texts:
        return []

    if isinstance(texts, str):
        texts = [texts]

    model = get_embedding_model()

    try:
        vectors = model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True   # 🔑 improves FAISS quality
        )

        # Ensure float32 for FAISS
        return [vec.astype(np.float32) for vec in vectors]

    except Exception as e:
        logger.exception("❌ Embedding generation failed")
        return []   # IMPORTANT: never crash API
