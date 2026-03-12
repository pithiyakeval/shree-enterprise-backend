import os
import logging
from groq import Groq
from dotenv import load_dotenv
from fastapi.concurrency import run_in_threadpool

load_dotenv()

logger = logging.getLogger("ai_llm")

GROQ_API_KEY=os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY missing")


client=Groq(
    api_key=GROQ_API_KEY,
    timeout=20
)


MODEL="llama-3.1-8b-instant"

TEMPERATURE=0.1

MAX_TOKENS=200

TOP_P=0.9

MAX_PROMPT_CHARS=5000

RETRIES=2


def safe_prompt(prompt:str):

    if len(prompt)>MAX_PROMPT_CHARS:

        logger.warning("Prompt truncated")

        return prompt[:MAX_PROMPT_CHARS]

    return prompt



def _call_llm(prompt:str):

    return client.chat.completions.create(

        model=MODEL,

        messages=[

            {
                "role":"user",
                "content":prompt
            }

        ],

        temperature=TEMPERATURE,

        max_tokens=MAX_TOKENS,

        top_p=TOP_P

    )



async def generate_answer(prompt:str)->str:

    prompt=safe_prompt(prompt)

    for i in range(RETRIES):

        try:

            completion=await run_in_threadpool(

                _call_llm,

                prompt

            )

            if completion and completion.choices:

                answer=completion.choices[0].message.content

                if answer:
                    return answer.strip()

        except Exception as e:

            logger.warning(f"LLM retry {i+1}")

            logger.warning(str(e))


    logger.error("LLM failed")

    return "Please contact Shree Enterprise for more details."