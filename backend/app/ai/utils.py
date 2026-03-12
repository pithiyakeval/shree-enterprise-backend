def detect_language(text: str) -> str:
    t = text.lower()

    # Gujarati Unicode
    for ch in text:
        if "\u0a80" <= ch <= "\u0aff":
            return "Gujarati"

    # Roman Gujarati keywords
    roman_gujarati = ["kem cho", "kem chho", "su che", "maja ma", "tame"]
    if any(w in t for w in roman_gujarati):
        return "Gujarati"

    return "English"


def is_greeting(text):

    greetings=[

        "hi",
        "hii",
        "hello",
        "hey",
        "namaste",
        "good morning",
        "good evening",
        "good afternoon",
        "hii ai",
        "hello ai",
        "hello there",
        


    ]

    t=text.lower().strip()

    return t in greetings