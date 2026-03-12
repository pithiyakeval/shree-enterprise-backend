
def format_answer(answer,contexts):

    answer=answer.strip()

    # normalize spacing
    answer=" ".join(answer.split())

    answer=clean_ai_phrases(answer)


    # unknown detection
    unknown_patterns=[

        "i don't have this information",
        "no information",
        "not available"

    ]

    if any(p in answer.lower() for p in unknown_patterns):

        return "I don't have this information. Please contact Shree Enterprise for assistance."


    # remove duplicate sentences
    sentences=answer.split(". ")

    unique=[]

    for s in sentences:

        s=s.strip()

        if s and s not in unique:

            unique.append(s)

    answer=". ".join(unique)


    # ensure ending dot
    if not answer.endswith("."):

        answer+="."


    # ---------- PREMIUM STRUCTURE ----------

    parts=answer.split(". ")

    if len(parts)>1:

        first=parts[0]

        rest=" ".join(parts[1:])

        answer=f"""{first}.

{rest}"""


    # add contact line if missing
    if "contact shree enterprise" not in answer.lower():

        answer=f"""{answer}

Please contact Shree Enterprise for complete details."""


    # ---------- SOURCES ----------

    sources=[]

    for c in contexts:

        src=c.get("source")

        if src and src not in sources:

            sources.append(src)


    if not sources:

        return answer


    source_text="\n".join(

        f"• {s.replace('_',' ').title()}"

        for s in sources

    )


    return f"""{answer}

Sources:
{source_text}"""

def clean_ai_phrases(text):

    bad_phrases=[

        "here is an improved version",
        "i made the following change",
        "improved answer",
        "rewritten answer",
        "reference information",
        "available systems"

    ]

    text=text.lower()

    for p in bad_phrases:

        text=text.replace(p,"")

    return text.strip()