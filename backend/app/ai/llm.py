import httpx

LLM_URL = "http://host.docker.internal:9000/generate"


def generate(prompt:str) -> str:
    r = httpx.post(
        LLM_URL,
        json={"prompt":prompt},
        timeout=60,
    
    )

    r.raise_for_status()
    return r.json()["text"]
