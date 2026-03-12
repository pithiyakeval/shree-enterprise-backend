from app.ai.llm_groq import generate_answer


async def improve_answer(answer:str):

    prompt=f"""

Rewrite this business answer to sound professional and natural.

Rules:

Do NOT explain changes.
Do NOT add commentary.
Do NOT say "improved version".
Do NOT add extra text.
Return ONLY the final answer.

Make it:

Clear
Short
Professional
Customer friendly
Maximum 4 sentences.

Answer:
{answer}

Final answer:

"""

    try:

        improved=await generate_answer(prompt)

        if improved:

            # remove accidental prefixes
            improved=improved.replace(
                "Here's an improved version:",
                ""
            )

            improved=improved.replace(
                "Improved answer:",
                ""
            )

            return improved.strip()

    except:
        pass

    return answer