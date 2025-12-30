import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.database import engine, Base
from backend.app.routers import lead, admin
from backend.app.config import settings
from backend.app.middleware.cleaner import CleanEmptyStringsMiddleware

# ================================================================
# LOGGING
# ================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(asctime)s] %(name)s → %(message)s",
)
logger = logging.getLogger("shree_backend")

# ================================================================
# FASTAPI APP
# ================================================================

app = FastAPI(
    title="Shree Enterprise Backend",
    version="1.0.0",
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_DOCS else None,
)

# ================================================================
# MIDDLEWARES
# ================================================================

app.add_middleware(CleanEmptyStringsMiddleware)

# 🌍 CORS (Env-based)
if settings.ENVIRONMENT == "dev":
    origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
else:
    origins = [settings.FRONTEND_URL]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================================================
# GLOBAL ERROR HANDLER
# ================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server error")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error"},
    )

# ================================================================
# STARTUP
# ================================================================

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Backend starting (%s mode)", settings.ENVIRONMENT)

    if settings.ENVIRONMENT == "dev":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("DB tables created (DEV mode)")

    logger.info("Backend ready")

# ================================================================
# ROUTERS
# ================================================================

app.include_router(lead.router)
app.include_router(admin.router)

# 🚫 IMPORTANT:
# AI ROUTES ARE ENABLED ONLY IN DEV
# (Render free tier cannot install numpy / LLM deps)

if settings.ENVIRONMENT == "dev":
    from backend.app.ai import chat_router
    app.include_router(chat_router.router)
    logger.info("AI routes enabled (DEV only)")
else:
    logger.info("AI routes disabled (PRODUCTION)")

# ================================================================
# HEALTH CHECK
# ================================================================

@app.get("/api/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
    }
