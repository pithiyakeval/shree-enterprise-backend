from app.ai.llm_groq import generate_answer


async def rewrite_query(question:str,history:str=""):

    prompt=f"""

Rewrite the user question to improve document search.

Rules:

Keep same meaning.
Add missing business keywords.
Make question complete.
Return ONLY rewritten question.

Conversation:
{history}

User question:
{question}

Rewritten question:

"""

    try:

        rewritten=await generate_answer(prompt)

        if rewritten and len(rewritten)<200:

            return rewritten.strip()

    except:
        pass

    return question