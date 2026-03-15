import logging
import time

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.database import verify_db_connection, close_db
from app.routers import lead, admin
from app.config import settings
from app.middleware.cleaner import CleanEmptyStringsMiddleware
from app.ai.qdrant_store import init_collection
from app.ai.embeddings import warmup_embeddings


# ==========================================================
# SAFE AI IMPORT
# ==========================================================

try:
    from app.ai.chat import router as ai_router
    AI_ENABLED = True

except Exception as e:

    AI_ENABLED = False

    logging.warning(f"AI disabled: {e}")


# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(

    level=logging.INFO,

    format="%(levelname)s [%(asctime)s] %(name)s → %(message)s",

)

logger = logging.getLogger("shree_backend")


# ==========================================================
# FASTAPI INIT
# ==========================================================

app = FastAPI(

    title=settings.APP_NAME,

    version="1.0.0",

    docs_url="/docs" if settings.ENABLE_DOCS else "/docs",

    redoc_url="/redoc" if settings.ENABLE_DOCS else None,

)


# ==========================================================
# CORS (SINGLE SOURCE FROM CONFIG)
# ==========================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=settings.cors_origins(),

    allow_origin_regex=r"https://.*",

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]

)


# ==========================================================
# TRUSTED HOST (AFTER CORS)
# ==========================================================

app.add_middleware(

    TrustedHostMiddleware,

    allowed_hosts=[

        "shreeenterprise.live",

        "www.shreeenterprise.live",

        "*.vercel.app",

        "*.onrender.com",

        "localhost",

        "127.0.0.1",

        "*"

    ]

)


# ==========================================================
# OTHER MIDDLEWARE
# ==========================================================

app.add_middleware(

    CleanEmptyStringsMiddleware

)


# ==========================================================
# FAST OPTIONS HANDLER (SAFE VERSION)
# ==========================================================

@app.middleware("http")
async def cors_preflight_fix(request: Request, call_next):

    if request.method == "OPTIONS":

        response = Response(status_code=200)

        response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin","*")

        response.headers["Access-Control-Allow-Methods"] = "*"

        response.headers["Access-Control-Allow-Headers"] = "*"

        response.headers["Access-Control-Allow-Credentials"] = "true"

        return response

    return await call_next(request)


# ==========================================================
# REQUEST TIMER
# ==========================================================

@app.middleware("http")
async def process_time(request: Request, call_next):

    start = time.time()

    response = await call_next(request)

    duration = round(time.time() - start,3)

    response.headers["X-Process-Time"] = str(duration)

    return response


# ==========================================================
# GLOBAL ERROR HANDLER
# ==========================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):

    logger.exception("Unhandled server error")

    return JSONResponse(

        status_code=500,

        content={"error":"Internal Server Error"}

    )


# ==========================================================
# STARTUP
# ==========================================================

@app.on_event("startup")
async def startup_event():

    logger.info(f"Backend starting ({settings.ENVIRONMENT})")

    await verify_db_connection()

    try:

        init_collection()

        warmup_embeddings()

        logger.info("AI initialized")

    except Exception as e:

        logger.warning(f"AI warmup skipped: {e}")

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

    prefix=settings.API_V1_PREFIX

)

app.include_router(

    admin.router,

    prefix=settings.API_V1_PREFIX

)

if AI_ENABLED:

    app.include_router(

        ai_router,

        prefix=settings.API_V1_PREFIX

    )


# ==========================================================
# HEALTH
# ==========================================================

@app.get(settings.HEALTH_PATH)
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