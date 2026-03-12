CONTACT_WORDS=[

"contact",
"number",
"phone",
"mobile",
"call",
"whatsapp"

]

ADDRESS_WORDS=[

"address",
"location",
"where",
"office"

]

PRICE_WORDS=[

"price",
"cost",
"charges"

]

SOLAR_WORDS=[

"solar",
"panel",
"installation"
"maintanance"

]

MANDAP_WORDS=[

"mandap",
"decoration",
"wedding"

]


def detect_intent(question):

    q=question.lower()

    if any(w in q for w in CONTACT_WORDS):

        return "contact"

    if any(w in q for w in ADDRESS_WORDS):

        return "address"

    if any(w in q for w in PRICE_WORDS):

        return "price"

    if any(w in q for w in SOLAR_WORDS):

        return "solar"

    if any(w in q for w in MANDAP_WORDS):

        return "mandap"

    return None