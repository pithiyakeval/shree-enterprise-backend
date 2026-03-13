import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.ai.qdrant_store import init_collection
from app.database import verify_db_connection, close_db
from app.routers import lead, admin
from app.config import settings
from app.middleware.cleaner import CleanEmptyStringsMiddleware
from app.ai.embeddings import warmup_embeddings

# AI router safe import
try:

    from app.ai.chat import router as ai_router

    AI_ENABLED=True

except Exception as e:

    AI_ENABLED=False

    logging.warning(f"AI disabled: {e}")


# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(

    level=logging.INFO,

    format="%(levelname)s [%(asctime)s] %(name)s → %(message)s",

)

logger=logging.getLogger("shree_backend")


# ==========================================================
# FASTAPI INIT
# ==========================================================

app=FastAPI(

    title="Shree Enterprise Backend",

    version="1.0.0",

    docs_url="/docs" if settings.ENABLE_DOCS else None,

    redoc_url="/redoc" if settings.ENABLE_DOCS else None,

)


# ==========================================================
# MIDDLEWARE
# ==========================================================

app.add_middleware(
    CleanEmptyStringsMiddleware
)


# ==========================================================
# CORS FIX ⭐
# ==========================================================

if settings.ENVIRONMENT=="dev":

    origins=[

        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8081",
        "http://127.0.0.1:8081"

    ]

else:

    origins=[

        settings.FRONTEND_URL,
        "https://www.shreeenterprise.live",
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "http://localhost:5173"

    ]


app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)


# ==========================================================
# REQUEST TIMER
# ==========================================================

@app.middleware("http")

async def add_process_time_header(request:Request, call_next):

    start=time.time()

    response=await call_next(request)

    duration=round(time.time()-start,3)

    response.headers["X-Process-Time"]=str(duration)

    return response


# ==========================================================
# GLOBAL ERROR HANDLER
# ==========================================================

@app.exception_handler(Exception)

async def global_exception_handler(request:Request, exc:Exception):

    logger.exception("Unhandled server error")

    return JSONResponse(

        status_code=500,

        content={"error":"Internal Server Error"},

    )


# ==========================================================
# STARTUP
# ==========================================================

@app.on_event("startup")
async def startup_event():

    logger.info(
        f"Backend starting ({settings.ENVIRONMENT})"
    )

    # Database check
    await verify_db_connection()
    warmup_embeddings()

    # Qdrant init ⭐
    try:

        init_collection()

        logger.info("Qdrant ready")

    except Exception as e:

        logger.error("Qdrant init failed")

        raise

    logger.info("Backend ready")
# ==========================================================
# SHUTDOWN
# ==========================================================

@app.on_event("shutdown")

async def shutdown_event():

    await close_db()

    logger.info("Backend stopped")


# ==========================================================
# ROUTES
# ==========================================================

app.include_router(
    lead.router,
    prefix="/api"
)

app.include_router(
    admin.router,
    prefix="/api"
)


if AI_ENABLED:

    app.include_router(ai_router)


# ==========================================================
# HEALTH
# ==========================================================

@app.get("/health")

async def health():

    return {

        "status":"ok",
        "environment":settings.ENVIRONMENT,
        "ai_enabled":AI_ENABLED

    }


# ==========================================================
# ROOT
# ==========================================================

@app.get("/")

async def root():

    return {

        "service":"Shree Enterprise API",
        "status":"running"

    }