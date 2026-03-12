import time
import logging
import numpy as np

from app.ai.embeddings import embed_query

logger = logging.getLogger("ai_semantic_cache")

# ==========================================================
# CACHE STORAGE
# ==========================================================

SEMANTIC_CACHE=[]

CACHE_TTL=900   # 15 min
SIM_THRESHOLD=0.92


# ==========================================================
# COSINE SIMILARITY
# ==========================================================

def cosine(a,b):

    a=np.array(a)
    b=np.array(b)

    if len(a)==0 or len(b)==0:

        return 0

    return float(

        np.dot(a,b)/

        (

            np.linalg.norm(a)*

            np.linalg.norm(b)+1e-10

        )

    )


# ==========================================================
# CLEAN OLD CACHE
# ==========================================================

def cleanup():

    now=time.time()

    SEMANTIC_CACHE[:] = [

        item for item in SEMANTIC_CACHE

        if now-item["time"]<CACHE_TTL

    ]


# ==========================================================
# LOOKUP
# ==========================================================

def semantic_lookup(question):

    if not SEMANTIC_CACHE:

        return None

    try:

        q_vec=embed_query(question)

        best=None
        best_score=0

        for item in SEMANTIC_CACHE:

            sim=cosine(

                q_vec,

                item["vector"]

            )

            if sim>SIM_THRESHOLD and sim>best_score:

                best=item
                best_score=sim

        if best:

            logger.info(

                f"Semantic cache hit {round(best_score,3)}"

            )

            return best["answer"]

        return None

    except Exception:

        logger.exception(

            "Semantic cache failed"

        )

        return None


# ==========================================================
# STORE
# ==========================================================

def semantic_store(

    question,
    answer

):

    try:

        cleanup()

        vector=embed_query(

            question

        )

        SEMANTIC_CACHE.append(

            {

                "question":question,

                "answer":answer,

                "vector":vector,

                "time":time.time()

            }

        )

    except Exception:

        logger.exception(

            "Semantic store failed"

        )