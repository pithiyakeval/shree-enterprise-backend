from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
import time
import asyncio
from app.ai.ai_loader import ensure_ai
from app.ai.formatter import format_answer, clean_ai_phrases
from app.ai.retriever import retrieve
from app.ai.prompt_templates import build_prompt
from app.ai.llm_groq import generate_answer
from app.ai.intent_router import detect_intent

from app.ai.utils import detect_language, is_greeting
from app.ai.query_rewriter import rewrite_query
from app.ai.reranker import rerank
from app.ai.answer_polisher import polish_answer

from app.ai.semantic_cache import (
    semantic_lookup,
    semantic_store
)

from app.ai.memory import (
    create_session,
    add_message,
    get_history_text,
    get_session
)

logger=logging.getLogger("ai_chat")

router=APIRouter(
    prefix="/api/ai",
    tags=["ai"]
)

# ==========================================================
# SHORT QUERY EXPANSION ⭐
# ==========================================================

SHORT_QUERY_MAP={

"contact":"shree enterprise contact number",
"phone":"shree enterprise contact number",
"number":"shree enterprise contact number",

"address":"shree enterprise address",
"location":"shree enterprise address",

"price":"solar panel price",
"cost":"solar price",

"solar":"solar panel installation service",
"mandap":"mandap decoration service"

}

# ==========================================================
# SYNONYMS ⭐
# ==========================================================

SYNONYMS={

"mobile":"contact",
"call":"contact",
"whatsapp":"contact",

"where":"address",
"office":"address",

"charges":"price",
"cost":"price"

}

# ==========================================================
# FAQ FAST PATH ⭐
# ==========================================================

FAQ_FAST={

"do you install solar":

"Yes, Shree Enterprise provides solar panel installation from 2.5kW to 5kW. Please contact us for pricing details.",

"do you provide maintenance":

"Yes, Shree Enterprise provides solar maintenance services after installation.",

"mandap price":

"Mandap decoration typically ranges from ₹30,000 to ₹50,000 depending on event requirements. Please contact us for details."

}

# ==========================================================
# SIMPLE CACHE
# ==========================================================

CACHE={}
CACHE_TTL=300


def get_cached(key):

    item=CACHE.get(key)

    if not item:
        return None

    if time.time()-item["time"]>CACHE_TTL:

        del CACHE[key]

        return None

    return item["answer"]


def set_cache(key,answer):

    CACHE[key]={

        "answer":answer,
        "time":time.time()

    }

# ==========================================================
# GUARDRAILS
# ==========================================================

def guardrail(answer):

    bad_words=[

        "maybe",
        "probably",
        "i think",
        "might be",
        "could be"

    ]

    for w in bad_words:

        if w in answer.lower():

            return "Please contact Shree Enterprise for accurate information."

    return answer


def unknown_filter(answer):

    patterns=[

        "i don't know",
        "no information",
        "not available",
        "not sure"

    ]

    for p in patterns:

        if p in answer.lower():

            return "I don't have this information. Please contact Shree Enterprise for assistance."

    return answer


def question_blocker(answer):

    if "?" in answer:

        return "Please contact Shree Enterprise for complete details."

    return answer


BUSINESS_KEYWORDS=[

"solar",
"panel",
"mandap",
"decoration",
"price",
"cost",
"maintenance",
"service",
"installation",
"warranty",
"brand",
"kw",
"subsidy",
"contact",
"address"

]


def scope_filter(question,history):

    q=question.lower()

    if any(word in q for word in BUSINESS_KEYWORDS):
        return True

    if len(q.split())<=3 and history:
        return True

    return False


# ==========================================================
# REQUEST MODEL
# ==========================================================

class ChatRequest(BaseModel):

    question:str
    session_id:str | None=None


# ==========================================================
# CONTEXT CLEANER
# ==========================================================

def clean_contexts(contexts):

    seen=set()
    clean=[]

    total_chars=0
    MAX_CONTEXT_CHARS=1500

    for c in contexts:

        text=c.get("text")

        if not text:
            continue

        if text in seen:
            continue

        if total_chars+len(text)>MAX_CONTEXT_CHARS:
            break

        seen.add(text)

        clean.append(c)

        total_chars+=len(text)

    clean.sort(

        key=lambda x:x.get("score",0),

        reverse=True

    )

    return clean[:2]


# ==========================================================
# CHAT ENDPOINT
# ==========================================================

@router.post("/chat")

async def chat(req:ChatRequest):

    start=time.time()

    question=req.question.strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question empty"
        )

    # SESSION

    if not req.session_id:

        session_id=create_session()

    else:

        session_id=req.session_id

        if not get_session(session_id):

            session_id=create_session()

    # GREETING

    if is_greeting(question):

        return {

            "answer":

"""Hello! I am Shree Enterprise AI Assistant.

I can help with:

• Solar installation
• Mandap decoration
• Pricing
• Contact details

How can I help you today?""",

            "session_id":session_id

        }

    # HISTORY

    history=get_history_text(session_id)

    history=history[-800:]

    # SYNONYM NORMALIZATION ⭐

    q_lower=question.lower()

    for word,replacement in SYNONYMS.items():

        if word in q_lower:

            question=q_lower.replace(word,replacement)

    # SHORT QUERY EXPANSION ⭐

    if question.lower() in SHORT_QUERY_MAP:

        search_question=SHORT_QUERY_MAP[question.lower()]

    else:

        search_question=question

    # FAQ FAST PATH ⭐

    if question.lower() in FAQ_FAST:

        return {

            "answer":FAQ_FAST[question.lower()],
            "session_id":session_id

        }

    # INTENT ROUTER ⭐

    intent=detect_intent(question)

    if intent=="contact":

        return {

"answer":

"""You can contact Shree Enterprise here:

Phone: 9898812423  
Email: jagdishbhai.pithiya@gmail.com  

Location:
Main Chowk Nagichana
Mangrol Junagadh""",

        "session_id":session_id

        }

    if intent=="address":

        return {

"answer":

"""Shree Enterprise address:

Main Chowk Nagichana  
Taluka Mangrol  
District Junagadh  

Please contact before visiting.""",

        "session_id":session_id

        }

    # SCOPE FILTER

    if not scope_filter(question,history):

        return {

            "answer":

            "I can only help with Shree Enterprise services like solar installation and mandap decoration.",

            "session_id":session_id

        }

    # QUERY REWRITE

    try:

        search_question=await rewrite_query(

            search_question,
            history

        )

    except:

        pass

    # CACHE

    cache_key=search_question.lower().strip()

    cached=get_cached(cache_key)

    if cached:

        return {

            "answer":cached,
            "cached":True,
            "session_id":session_id

        }

    # SEMANTIC CACHE

    semantic=semantic_lookup(search_question)

    if semantic:

        return {

            "answer":semantic,
            "session_id":session_id

        }
    

    # RETRIEVE

    try:
        ensure_ai()
        contexts=retrieve(

            search_question,
            history

        )

        try:
            contexts=rerank(search_question,contexts)
        except:
            pass

        contexts=clean_contexts(contexts)

    except:

        contexts=[]

    if not contexts:

        return {

            "answer":

            """I can help with:

• Solar installation
• Mandap decoration
• Pricing
• Contact details

Please ask a service related question.""",

            "session_id":session_id

        }

    # PROMPT

    try:

        prompt=build_prompt(

            question=question,
            contexts=contexts,
            history=history

        )

    except:

        prompt=question

    # LLM

    try:

        answer=await asyncio.wait_for(

            generate_answer(prompt),

            timeout=10

        )

        answer=guardrail(answer)

        answer=unknown_filter(answer)

        answer=question_blocker(answer)

    except:

        answer="Please contact Shree Enterprise for details."

    # FORMAT

    answer=clean_ai_phrases(answer)

    formatted=format_answer(

        answer,
        contexts

    )

    formatted=polish_answer(

        formatted

    )

    # CACHE STORE

    set_cache(

        cache_key,
        formatted

    )

    semantic_store(

        search_question,
        formatted

    )

    # MEMORY

    add_message(

        session_id,
        question,
        formatted

    )

    duration=round(

        time.time()-start,
        2

    )

    return {

        "answer":formatted,
        "session_id":session_id,
        "contexts":len(contexts),
        "response_time":duration

    }