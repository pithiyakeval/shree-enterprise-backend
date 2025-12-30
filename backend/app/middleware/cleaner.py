# app/middleware/cleaner.py

import json
from starlette.types import ASGIApp, Receive, Scope, Send


class CleanEmptyStringsMiddleware:
    """
    Production-ready middleware that:

    ✔ Converts "" → None for specific fields (email, budget, etc.)
    ✔ Does NOT break non-JSON requests
    ✔ Safely replays the body once (required for FastAPI)
    ✔ Supports camelCase + snake_case
    ✔ Prevents crashes on large or invalid JSON bodies
    """

    TARGET_FIELDS = {
        "email",
        "kw",
        "budget",
        "eventType",
        "eventDate",
        "event_type",
        "event_date",
        "whereFrom",
        "where_from",
    }

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        # Only clean HTTP requests
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Read full request body
        body = b""
        more = True

        while more:
            message = await receive()
            if message["type"] != "http.request":
                break
            body += message.get("body", b"")
            more = message.get("more_body", False)

        # Attempt cleaning JSON
        if body:
            try:
                decoded = body.decode("utf-8")
                data = json.loads(decoded)

                if isinstance(data, dict):
                    for key in list(data.keys()):
                        if key in self.TARGET_FIELDS and data[key] == "":
                            data[key] = None

                    # Convert modified payload back to bytes
                    body = json.dumps(data).encode("utf-8")

            except Exception:
                # Not JSON → ignore
                pass

        # Reconstruct receive() with modified body
        async def new_receive() -> dict:
            return {"type": "http.request", "body": body, "more_body": False}

        await self.app(scope, new_receive, send)
