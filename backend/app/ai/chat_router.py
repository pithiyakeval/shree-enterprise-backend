from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import numpy as np
import logging

from app.ai.vectorestore import load_index
from app.ai.embeddings import embed_texts
from app.ai.prompt_templates import build_prompt
from app.ai.llm import generate
from app.ai.utils import detect_language, is_greeting

logger = logging.getLogger("ai_chat")

router = APIRouter(prefix="/api/ai", tags=["ai"])

# =================================================
# Load FAISS index ONCE (startup safe)
# =================================================
INDEX, METAS = load_index()
if INDEX is None or not METAS:
    logger.warning("FAISS index not loaded. RAG disabled.")


# =================================================
# Request schema
# =================================================
class ChatRequest(BaseModel):
    question: str


# =================================================
# Safe FAISS search
# =================================================
def search_docs(query: str, top_k: int = 4):
    if INDEX is None or not METAS:
        return []

    language = detect_language(query)

    try:
        embedding = embed_texts([query])[0]  # (dim,)
        vector = np.array([embedding], dtype=np.float32)  # (1, dim)
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return []

    try:
        distances, indices = INDEX.search(vector, top_k * 2)
    except Exception as e:
        logger.error(f"FAISS search failed: {e}")
        return []

    results = []
    for score, idx in zip(distances[0], indices[0]):
        if idx < 0 or idx >= len(METAS):
            continue

        meta = METAS[idx]
        if meta.get("language") != language:
            continue

        results.append(
            {
                "text": meta.get("text", ""),
                "metadata": meta,
                "distance": float(score),
            }
        )

        if len(results) >= top_k:
            break

    return results


# =================================================
# Chat endpoint
# =================================================
@router.post("/chat")
async def chat(req: ChatRequest):
    question = req.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # -------------------------------------------------
    # 1️⃣ Greeting (NO LLM)
    # -------------------------------------------------
    if is_greeting(question):
        lang = detect_language(question)
        if lang == "Gujarati":
            return {
                "answer": "નમસ્તે! હું Shree Enterprise Assistant છું. હું તમને કેવી રીતે મદદ કરી શકું?"
            }
        return {
            "answer": "Hello! I am the Shree Enterprise Assistant. How can I help you today?"
        }

    # -------------------------------------------------
    # 2️⃣ RAG + LLM
    # -------------------------------------------------
    contexts = search_docs(question)
    prompt = build_prompt(question, contexts)

    try:
        answer = generate(prompt)

        # ✅ Accept only meaningful answers
        if answer and len(answer.strip()) > 15:
            return {"answer": answer.strip()}

        # Weak output → fallback
        raise RuntimeError("Weak LLM output")

    except Exception as e:
        logger.error(f"LLM failed: {e}")

        # -------------------------------------------------
        # 3️⃣ Safe business fallback (NO crash)
        # -------------------------------------------------
        lang = detect_language(question)

        if lang == "Gujarati":
            return {
                "answer": (
                    "Shree Enterprise સોલાર પેનલ ઇન્સ્ટોલેશન અને "
                    "મંડપ ડેકોરેશન સેવાઓ આપે છે. "
                    "વધુ માહિતી માટે કૃપા કરીને અમારી ટીમનો સંપર્ક કરો."
                )
            }

        return {
            "answer": (
                "Shree Enterprise provides solar panel installation and "
                "mandap decoration services. "
                "Please contact our team for accurate details."
            )
        }
