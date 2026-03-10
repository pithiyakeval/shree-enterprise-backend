# app/routers/lead.py

from fastapi import (
    APIRouter,
    Depends,
    BackgroundTasks,
    status,
    Request,
    HTTPException,
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import BaseLeadCreate, BaseLeadOut
from app.crud import create_lead_with_service
from app.utils import (
    send_owner_notification_email,
    send_user_confirmation_email,
)
import logging
import re
import time


router = APIRouter(prefix="/api/lead", tags=["lead"])

logger = logging.getLogger("lead_logger")

RATE_LIMIT = {}
LIMIT_SECONDS = 15


def rate_limit_check(ip: str):
    now = time.time()
    last = RATE_LIMIT.get(ip, 0)
    if now - last < LIMIT_SECONDS:
        raise HTTPException(
            status_code=429,
            detail="Too many submissions. Please wait and try again.",
        )
    RATE_LIMIT[ip] = now


@router.post(
    "/submit",
    response_model=BaseLeadOut,
    status_code=status.HTTP_201_CREATED,
)
async def submit_lead(
    request: Request,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # 1️⃣ Rate limit
    client_ip = request.client.host
    rate_limit_check(client_ip)

    # 2️⃣ Parse JSON
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Body must be JSON object")

    # 3️⃣ Normalize camelCase → snake_case
    mapping = {
        "whereFrom": "where_from",
        "eventType": "event_type",
        "eventDate": "event_date",
    }
    normalized = {mapping.get(k, k): v for k, v in data.items()}

    # 4️⃣ Clean optional fields
    for field in ("email", "kw", "budget", "event_type", "event_date"):
        if normalized.get(field) in ("", None):
            normalized[field] = None

    # 5️⃣ Default source
    normalized.setdefault("where_from", "contact")

    # 6️⃣ Phone validation
    phone = normalized.get("phone", "")
    if not re.fullmatch(r"[0-9+\- ]{7,15}", phone):
        raise HTTPException(status_code=400, detail="Invalid phone number")

    # 7️⃣ Pydantic validation
    try:
        lead = BaseLeadCreate(**normalized)
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=422, detail=str(e))

    # 8️⃣ Save lead
    new_lead = await create_lead_with_service(db, lead)

    # 9️⃣ Owner email content
    owner_subject = f"New {lead.service} Lead from {lead.where_from}"
    owner_message = (
        f"Name: {lead.name}\n"
        f"Phone: {lead.phone}\n"
        f"Email: {lead.email}\n"
        f"City: {lead.city}\n"
        f"Service: {lead.service}\n"
        f"KW: {lead.kw}\n"
        f"Budget: {lead.budget}\n"
        f"Event Type: {lead.event_type}\n"
        f"Event Date: {lead.event_date}\n"
        f"Message: {lead.message}\n"
        f"Source: {lead.where_from}\n"
    )

    # 🔟 Owner notification (ONE FUNCTION)
    background.add_task(
        send_owner_notification_email,
        owner_subject,
        owner_message,
    )

    # 1️⃣1️⃣ User confirmation (SEPARATE FUNCTION)
    if lead.email:
        background.add_task(
            send_user_confirmation_email,
            lead.email,
            lead.name,
        )

    logger.info(f"Lead submitted → {lead.service} from {client_ip}")

    return new_lead
