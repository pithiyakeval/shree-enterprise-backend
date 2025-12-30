import re

FORBIDDEN_PATTERNS = [
    r"\[.*?\]",                # removes [anything]
    r"Owner contact numbers",
    r"Developer contact",
    r"Website:",
    r"http[s]?://\S+",
]

def sanitize_answer(text: str) -> str:
    if not text:
        return ""

    cleaned = text

    for pattern in FORBIDDEN_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Remove repeated spaces / newlines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)

    return cleaned.strip()
