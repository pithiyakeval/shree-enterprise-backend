"""
Production embedding service for Shree Enterprise AI

Features:
✔ Singleton model load (no reload per request)
✔ HuggingFace cache support (Render safe)
✔ Memory safe normalization
✔ Query cache (faster repeated queries)
✔ Cloud deployment ready
✔ Startup warm loading supported
"""

import os
import logging
import numpy as np
from typing import List, Union, Optional
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("ai_embeddings")


# ==========================================================
# CONFIG
# ==========================================================

EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "BAAI/bge-small-en-v1.5"
)

# IMPORTANT → use hf-cache not ai_models
HF_CACHE_DIR = os.getenv(
    "HF_CACHE_DIR",
    "./hf-cache"
)

DEVICE = os.getenv(
    "EMBEDDING_DEVICE",
    "cpu"
)

# Prevent memory explosion
MAX_CACHE = 1000

# Query embedding cache
EMBED_CACHE: dict[str, List[float]] = {}


# ==========================================================
# MODEL SINGLETON
# ==========================================================

_model: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    """
    Load embedding model once.
    Production safe singleton.
    """

    global _model

    if _model:
        return _model

    try:

        logger.info(f"Loading embedding model → {EMBEDDING_MODEL_NAME}")

        _model = SentenceTransformer(

            EMBEDDING_MODEL_NAME,

            cache_folder=HF_CACHE_DIR,

            device=DEVICE

        )

        logger.info("Embedding model ready")

        return _model

    except Exception as e:

        logger.exception("Embedding model failed")

        raise RuntimeError(
            "Embedding model initialization failed"
        ) from e


# ==========================================================
# BULK EMBEDDINGS
# ==========================================================

def embed_texts(
    texts: Union[str, List[str]]
) -> List[List[float]]:
    """
    Generate embeddings for list.
    Always returns float32 vectors.
    """

    if not texts:
        return []

    if isinstance(texts, str):
        texts=[texts]

    model=get_embedding_model()

    try:

        vectors=model.encode(

            texts,

            convert_to_numpy=True,

            normalize_embeddings=True,

            show_progress_bar=False,

            batch_size=32

        )

        return vectors.astype(np.float32).tolist()

    except Exception:

        logger.exception("Embedding generation failed")

        return []


# ==========================================================
# QUERY EMBEDDING
# ==========================================================

def embed_query(text:str)->List[float]:
    """
    Optimized single query embedding.
    Uses small cache.
    """

    if not text:
        return []

    # cache hit
    if text in EMBED_CACHE:
        return EMBED_CACHE[text]

    vectors=embed_texts(text)

    if not vectors:
        return []

    vector=vectors[0]

    # Prevent cache overflow
    if len(EMBED_CACHE) > MAX_CACHE:

        EMBED_CACHE.clear()

        logger.info("Embedding cache cleared")

    EMBED_CACHE[text]=vector

    return vector


# ==========================================================
# STARTUP WARM LOAD
# ==========================================================

def warmup_embeddings():
    """
    Preload model during FastAPI startup.
    Prevents first request delay.
    """

    try:

        get_embedding_model()

        logger.info("Embedding model warmed")

    except Exception:

        logger.exception("Embedding warmup failed")