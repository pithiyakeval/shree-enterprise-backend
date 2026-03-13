import logging
from typing import List, Dict

from app.ai.embeddings import embed_query
from app.ai.qdrant_store import search_vectors
from app.ai.utils import detect_language

logger = logging.getLogger("ai_retriever")


# ==========================================================
# QUERY CLEANER
# ==========================================================

def clean_query(q: str):

    q = q.strip().lower()

    q = q.replace("?", "")
    q = q.replace(",", "")
    q = q.replace(".", "")

    return " ".join(q.split())


# ==========================================================
# QUERY EXPANSION
# ==========================================================

def expand_query(query: str):

    expansions = {

        "solar": "solar panel rooftop installation system",
        "price": "price cost installation solar panel",
        "mandap": "mandap decoration wedding tent services",
        "maintenance": "solar maintenance service repair",
    }

    words = query.split()

    expanded = [query]

    for w in words:

        if w in expansions:
            expanded.append(expansions[w])

    return " ".join(expanded)


# ==========================================================
# QUERY REWRITE (conversation aware)
# ==========================================================

def rewrite_query(query: str, history: str):

    if not history:
        return query

    q = query.lower()

    if len(q.split()) <= 2:

        if "price" in q or "cost" in q:

            if "solar" in history.lower():
                return "solar panel price"

            if "mandap" in history.lower():
                return "mandap decoration price"

        if "maintenance" in q:

            if "solar" in history.lower():
                return "solar panel maintenance service"

    return query


# ==========================================================
# TEXT NORMALIZER (duplicate killer)
# ==========================================================

def normalize_text(text):

    text = text.lower()

    text = text.replace("\n", " ")

    return " ".join(text.split())


# ==========================================================
# KEYWORD BOOST
# ==========================================================

def keyword_score(query, text):

    q = set(query.split())

    t = set(text.lower().split())

    matches = q.intersection(t)

    if not matches:
        return 0

    return min(len(matches) * 0.025, 0.10)


# ==========================================================
# SEMANTIC BOOST
# ==========================================================

def semantic_boost(query, text):

    important = ["solar", "installation", "price", "mandap", "maintenance"]

    score = 0

    for w in important:

        if w in query and w in text.lower():
            score += 0.02

    return score


# ==========================================================
# HYBRID SCORE
# ==========================================================

def hybrid_score(query, result):

    payload = result.get("payload") or {}

    text = payload.get("text", "")

    vector = float(result.get("score", 0))

    keyword = keyword_score(query, text)

    semantic = semantic_boost(query, text)

    return (vector * 0.85) + keyword + semantic


# ==========================================================
# LANGUAGE MATCH
# ==========================================================

def language_match(query_lang, payload_lang):

    if not payload_lang:
        return True

    payload_lang = payload_lang.lower()

    query_lang = query_lang.lower()

    if payload_lang.startswith("en") and query_lang.startswith("en"):
        return True

    if payload_lang.startswith("gu") and query_lang.startswith("gu"):
        return True

    return False


# ==========================================================
# RETRIEVER
# ==========================================================

def retrieve(

    query: str,

    history: str = "",

    k: int = 3

) -> List[Dict]:

    if not query:
        return []

    query = clean_query(query)

    query = rewrite_query(query, history)

    query = query + " shree enterprise solar mandap services"

    language = detect_language(query).lower()

    try:

        vector = embed_query(query)

        if not isinstance(vector, list):
            vector = vector.tolist()

    except Exception:

        logger.exception("Embedding failed")

        return []

    try:

        results = search_vectors(

            vector,

            top_k=40

        )

    except Exception:

        logger.exception("Vector search failed")

        return []

    if not results:
        return []

    results.sort(

        key=lambda x: hybrid_score(query, x),

        reverse=True

    )

    contexts = []

    seen_text = set()

    seen_source = set()

    seen_chunk = set()

    for r in results:

        payload = r.get("payload") or {}

        text = payload.get("text", "")

        if not text:
            continue

        normalized = normalize_text(text)

        if normalized in seen_text:
            continue

        score = hybrid_score(query, r)

        if score < 0.32:
            continue

        payload_lang = payload.get("language", "")

        if not language_match(language, payload_lang):
            continue

        if len(text) < 30:
            continue

        source = payload.get("source", "")

        chunk = payload.get("chunk_id")

        chunk_key = f"{source}_{chunk}"

        if chunk_key in seen_chunk:
            continue

        if source in seen_source and len(contexts) >= 1:
            continue

        seen_text.add(normalized)

        seen_source.add(source)

        seen_chunk.add(chunk_key)

        contexts.append({

            "text": text,

            "source": source,

            "score": round(score, 4),

            "chunk": chunk

        })

        if len(contexts) >= k:
            break

        # fallback if strict filters removed everything
        if not contexts and results:

            for r in results[:2]:

                payload=r.get("payload") or {}

                text=payload.get("text")

                if text:

                    contexts.append({

                        "text":text,
                        "source":payload.get("source"),
                        "score":0.30,
                        "chunk":payload.get("chunk_id")

                    })

    logger.info(f"Retriever returned {len(contexts)} contexts")

    return contexts