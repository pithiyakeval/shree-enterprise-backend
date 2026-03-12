import time
import uuid
import logging

logger = logging.getLogger("ai_memory")

# ==========================================================
# CONFIG
# ==========================================================

SESSION_TTL = 1800   # 30 min

MAX_HISTORY = 6      # last messages kept


# ==========================================================
# STORAGE
# ==========================================================

sessions = {}


# ==========================================================
# SESSION CREATOR
# ==========================================================

def create_session():

    session_id = str(uuid.uuid4())

    sessions[session_id] = {

        "history":[],

        "last":time.time()

    }

    return session_id


# ==========================================================
# GET SESSION
# ==========================================================

def get_session(session_id):

    if session_id not in sessions:

        return None

    # update activity
    sessions[session_id]["last"] = time.time()

    return sessions[session_id]


# ==========================================================
# ADD MESSAGE
# ==========================================================

def add_message(

    session_id,

    question,

    answer

):

    if session_id not in sessions:

        sessions[session_id] = {

            "history":[],

            "last":time.time()

        }

    history = sessions[session_id]["history"]

    history.append({

        "q":question,

        "a":answer

    })

    # keep last N only
    sessions[session_id]["history"] = history[-MAX_HISTORY:]


# ==========================================================
# GET HISTORY TEXT (for prompt)
# ==========================================================

def get_history_text(session_id):

    if session_id not in sessions:

        return ""

    history = sessions[session_id]["history"]

    if not history:

        return ""

    text = ""

    for h in history[-3:]:

        text += f"""
User: {h['q']}

Assistant: {h['a']}
"""

    return text


# ==========================================================
# CLEAN OLD SESSIONS
# ==========================================================

def cleanup():

    now = time.time()

    remove = []

    for sid,data in sessions.items():

        if now - data["last"] > SESSION_TTL:

            remove.append(sid)

    for sid in remove:

        del sessions[sid]

    if remove:

        logger.info(f"Cleaned {len(remove)} sessions")