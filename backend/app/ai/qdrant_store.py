# app/ai/qdrant_store.py

import os
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
)
import uuid
from app.config import settings

logger = logging.getLogger("ai_qdrant")


# ==========================================================
# CONFIG
# ==========================================================

QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "shree_docs")

QDRANT_URL = settings.QDRANT_URL
QDRANT_API_KEY = settings.QDRANT_API_KEY

if not QDRANT_URL:
    raise RuntimeError("QDRANT_URL not configured")

VECTOR_DIM = 384


# ==========================================================
# CLIENT SINGLETON
# ==========================================================

_client: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    """
    Production Qdrant client.
    Always connects to Docker server.
    """

    global _client

    if _client:

        try:
            _client.get_collections()
            return _client

        except:

            logger.warning("Reconnecting Qdrant")

            _client=None

    try:

        logger.info("Connecting to Qdrant cloud cluster")   

        _client = QdrantClient(

            url=QDRANT_URL,

            api_key=QDRANT_API_KEY,

            timeout=15,

            prefer_grpc=False

        )

        logger.info("Qdrant connected")

        return _client

    except Exception as e:

        logger.exception("Failed to connect Qdrant")

        raise RuntimeError("Qdrant initialization failed") from e


# ==========================================================
# COLLECTION INIT
# ==========================================================

def init_collection() -> None:

    client = get_qdrant_client()

    try:

        exists = client.collection_exists(QDRANT_COLLECTION)

        if exists:
            logger.info("Qdrant collection exists")
            return

        logger.info("Creating Qdrant collection")

        client.create_collection(

            collection_name=QDRANT_COLLECTION,

            vectors_config=VectorParams(
                size=VECTOR_DIM,
                distance=Distance.COSINE,
            ),

        )

        logger.info(f"Collection created: {QDRANT_COLLECTION}")

    except Exception:

        logger.exception("Collection init failed")

        raise
# ==========================================================
# UPSERT VECTORS
# ==========================================================

def upsert_vectors(
    vectors: List[List[float]],
    payloads: List[Dict[str, Any]],
) -> None:
    """
    Insert / update embeddings into Qdrant.
    """

    if not vectors:
        logger.warning("No vectors provided for upsert")
        return

    if len(vectors) != len(payloads):
        raise ValueError("Vector / payload mismatch")

    client = get_qdrant_client()

    try:

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vectors[i],
                payload=payloads[i],
            )
            for i in range(len(vectors))
        ]

        client.upsert(
            collection_name=QDRANT_COLLECTION,
            points=points,
        )

        logger.info(f"Upserted {len(points)} vectors")

    except Exception:
        logger.exception("Vector upsert failed")


# ==========================================================
# SEARCH
# ==========================================================

def search_vectors(
    query_vector: List[float],
    top_k: int = 40,
    source: str | None=None
) -> List[Dict[str, Any]]:
    
    filter_condition=None

    if source:

        filter_condition={

            "must":[

                {

                    "key":"source",

                    "match":{

                        "value":source

                    }

                }

            ]

        }

    if not query_vector:
        return []

    client = get_qdrant_client()

    try:

        query_args={

            "collection_name":QDRANT_COLLECTION,

            "query":query_vector,

            "limit":top_k,

            "with_payload":True,

            "with_vectors":False

        }

        if filter_condition:

            query_args["query_filter"]=filter_condition


        results = client.query_points(**query_args)

        clean=[]

        logger.info(f"Qdrant returned {len(clean)} results")

        for r in results.points:

            if r.score < 0.25:   # ⭐ ignore weak matches
                continue

            clean.append({

                "score": r.score,
                "payload": r.payload

            })

        return clean

    except Exception:

        logger.exception("Vector search failed")

        return []

# ==========================================================
# HEALTH CHECK
# ==========================================================

def qdrant_health() -> bool:
    """
    Check if Qdrant connection works.
    """

    try:
        client = get_qdrant_client()
        client.get_collections()
        return True
    except Exception:
        return False