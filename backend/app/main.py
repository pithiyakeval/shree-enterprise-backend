import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.ai.qdrant_store import init_collection
from app.database import verify_db_connection, close_db
from app.routers import lead, admin
from app.config import settings
from app.middleware.cleaner import CleanEmptyStringsMiddleware
from app.ai.embeddings import warmup_embeddings


# ==========================================================
# SAFE AI IMPORT
# ==========================================================

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

    docs_url="/docs" if settings.DEBUG else None,

    redoc_url="/redoc" if settings.DEBUG else None,

)


# ==========================================================
# MIDDLEWARE
# ==========================================================

# Clean empty strings
app.add_middleware(
    CleanEmptyStringsMiddleware
)


# ==========================================================
# CORS CONFIG (FINAL PRODUCTION SAFE)
# ==========================================================

DEV_ORIGINS=[

    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://localhost:8081"

]


PROD_ORIGINS=[

    "https://shreeenterprise.live",
    "https://www.shreeenterprise.live",
    "https://shree-enterprise-platform.vercel.app"

]


if settings.ENVIRONMENT.lower()=="dev":

    origins=DEV_ORIGINS

else:

    origins=PROD_ORIGINS + DEV_ORIGINS


app.add_middleware(

    CORSMiddleware,

    allow_origins=origins,

    allow_origin_regex=r"https://.*\.vercel\.app",

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

    max_age=86400

)


# ==========================================================
# TRUSTED HOSTS (SECURITY)
# ==========================================================

app.add_middleware(

    TrustedHostMiddleware,

    allowed_hosts=[

        "shreeenterprise.live",
        "www.shreeenterprise.live",
        "*.vercel.app",
        "localhost",
        "127.0.0.1"

    ]

)


# ==========================================================
# REQUEST TIMER MIDDLEWARE
# ==========================================================

@app.middleware("http")
async def process_timer(request:Request, call_next):

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

        content={

            "error":"Internal Server Error"

        }

    )


# ==========================================================
# STARTUP
# ==========================================================

@app.on_event("startup")
async def startup_event():

    logger.info(
        f"Backend starting ({settings.ENVIRONMENT})"
    )

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

    prefix="/api"

)


app.include_router(

    admin.router,

    prefix="/api"

)


if AI_ENABLED:

    app.include_router(

        ai_router,

        prefix="/api"

    )


# ==========================================================
# HEALTH CHECK
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