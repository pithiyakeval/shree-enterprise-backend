import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.database import engine, Base
from backend.app.routers import lead, admin
from backend.app.config import settings
from backend.app.middleware.cleaner import CleanEmptyStringsMiddleware

# ⚠️ AI router loaded lazily (important)
try:
    from backend.app.ai import chat_router
    AI_ENABLED = True
except Exception as e:
    AI_ENABLED = False
    logging.warning("AI disabled: %s", e)


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(asctime)s] %(name)s → %(message)s",
)
logger = logging.getLogger("shree_backend")


app = FastAPI(
    title="Shree Enterprise Backend",
    version="1.0.0",
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_DOCS else None,
)


app.add_middleware(CleanEmptyStringsMiddleware)

# =============================
# CORS
# =============================
origins = (
    [
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    if settings.ENVIRONMENT == "dev"
    else [settings.FRONTEND_URL]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server error")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error"},
    )


@app.on_event("startup")
async def startup_event():
    logger.info("Backend starting (%s)", settings.ENVIRONMENT)

    if settings.ENVIRONMENT == "dev":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    logger.info("Backend ready")


# =============================
# ROUTES
# =============================
app.include_router(lead.router)
app.include_router(admin.router)

if AI_ENABLED:
    app.include_router(chat_router.router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "env": settings.ENVIRONMENT,
        "ai_enabled": AI_ENABLED,
    }
