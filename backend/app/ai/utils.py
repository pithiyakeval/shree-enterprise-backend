def detect_language(text: str) -> str:
    t = text.lower()

    # Gujarati Unicode
    for ch in text:
        if "\u0A80" <= ch <= "\u0AFF":
            return "Gujarati"

    # Roman Gujarati keywords
    roman_gujarati = ["kem cho", "kem chho", "su che", "maja ma", "tame"]
    if any(w in t for w in roman_gujarati):
        return "Gujarati"

    return "English"


def is_greeting(text: str) -> bool:
    greetings = [
        "hi", "hello", "hey", "namaste",
        "kem cho", "kem chho", "kemcho",
        "ram ram", "jay shree krishna"
    ]
    t = text.lower().strip()
    return any(g in t for g in greetings)