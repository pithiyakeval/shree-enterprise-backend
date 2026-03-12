import logging
from typing import List, Dict
import numpy as np

from app.ai.embeddings import embed_query

logger = logging.getLogger("ai_reranker")


# ==========================================================
# COSINE SIMILARITY
# ==========================================================

def cosine_similarity(a, b):

    a = np.array(a)
    b = np.array(b)

    if len(a) == 0 or len(b) == 0:
        return 0

    return float(

        np.dot(a, b) /

        (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10)

    )


# ==========================================================
# RERANK CONTEXTS
# ==========================================================

def rerank(

    question:str,

    contexts:List[Dict],

    top_k:int=3

)->List[Dict]:

    if not contexts:
        return contexts

    try:

        q_vec = embed_query(question)

        scored=[]

        for c in contexts:

            text=c.get("text","")

            if not text:
                continue

            doc_vec=c.get("vector")

            # fallback if vector missing
            if not doc_vec:

                doc_vec=embed_query(text)

            sim=cosine_similarity(

                q_vec,

                doc_vec

            )

            # combine retriever score + semantic score
            final_score = (

                sim * 0.7 +

                c.get("score",0) * 0.3

            )

            c["rerank_score"]=final_score

            scored.append(c)


        scored.sort(

            key=lambda x:x.get(

                "rerank_score",

                0

            ),

            reverse=True

        )

        return scored[:top_k]


    except Exception:

        logger.exception(

            "Rerank failed"

        )

        return contexts[:top_k]