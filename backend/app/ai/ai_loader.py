import logging

from app.ai.embeddings import warmup_embeddings
from app.ai.qdrant_store import init_collection

logger=logging.getLogger("ai_loader")

AI_READY=False


def ensure_ai():

    global AI_READY

    if AI_READY:
        return

    try:

        logger.info("Loading AI models")

        warmup_embeddings()

        init_collection()

        AI_READY=True

        logger.info("AI ready")

    except Exception:

        logger.exception("AI load failed")