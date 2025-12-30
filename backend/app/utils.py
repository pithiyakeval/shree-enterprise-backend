# app/utils.py

import logging
import smtplib
import re
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from argon2 import PasswordHasher, exceptions as argon_exc

from app.config import settings


# ============================================================
# LOGGER — production safe
# ============================================================

logger = logging.getLogger("shree_backend")
logger.setLevel(logging.INFO)


# ============================================================
# PASSWORD HASHING (Argon2id)
# ============================================================

ph = PasswordHasher(
    time_cost=3,
    memory_cost=64 * 1024,  # 64MB
    parallelism=2,
    hash_len=32,
)


def get_password_hash(password: str) -> str:
    return ph.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        valid = ph.verify(hashed, plain)
        if ph.check_needs_rehash(hashed):
            logger.info("Password hash upgraded.")
        return valid
    except argon_exc.VerifyMismatchError:
        return False
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


# ============================================================
# JWT TOKENS
# ============================================================


def create_access_token(
    data: dict,
    expires_minutes: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES,
) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=expires_minutes)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict, days: int = 7) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(days=days)
    payload["scope"] = "refresh"
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        return None


# ============================================================
# EMAIL VALIDATION
# ============================================================


def is_valid_email(email: str) -> bool:
    """
    Simple RFC-safe email validation
    """
    return bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email))


# ============================================================
# LOW-LEVEL SMTP SENDER (DO NOT ADD BUSINESS LOGIC HERE)
# ============================================================


def _send_email_raw(to_email: str, subject: str, body: str) -> bool:
    """
    Sends a plain-text email via SMTP.
    Returns True on success, False on failure.
    """
    try:
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = settings.FROM_EMAIL
        msg["To"] = to_email

        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(settings.SMTP_HOST, int(settings.SMTP_PORT)) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.FROM_EMAIL, to_email, msg.as_string())

        logger.info(f"Email sent → {to_email}")
        return True

    except Exception as e:
        logger.error(f"Email send failed → {to_email} | {e}")
        return False


# ============================================================
# OWNER NOTIFICATION EMAIL (BACKGROUND SAFE)
# ============================================================


def send_owner_notification_email(subject: str, body: str) -> None:
    """
    Sends notification email to ALL owners defined in settings.OWNER_EMAILS
    Safe for FastAPI BackgroundTasks (never raises).
    """
    try:
        owner_emails = getattr(settings, "OWNER_EMAILS", "")

        if not owner_emails:
            logger.warning("OWNER_EMAILS not configured.")
            return

        email_list = [
            email.strip()
            for email in owner_emails.split(",")
            if is_valid_email(email.strip())
        ]

        if not email_list:
            logger.warning("No valid owner emails found.")
            return

        for email in email_list:
            _send_email_raw(email, subject, body)

    except Exception as e:
        logger.error(f"Owner notification email error: {e}")


# ============================================================
# USER CONFIRMATION EMAIL
# ============================================================


def send_user_confirmation_email(user_email: str, user_name: str) -> None:
    """
    Sends a clean, professional confirmation email to the user.
    """
    if not is_valid_email(user_email):
        logger.warning(f"Invalid user email skipped → {user_email}")
        return

    subject = "Thank You for Contacting Shree Enterprise"

    body = f"""Hello {user_name},

Thank you for contacting Shree Enterprise.

We have received your request and our team will get in touch with you shortly.

If you have any additional details to share, feel free to reply to this email.

Warm regards,
Shree Enterprise
"""

    _send_email_raw(user_email, subject, body)


def detect_language(text: str) -> str:
    """Detect Gujarati vs English using  Unicode range"""

    for ch in text:
        if "\u0a80" <= ch <= "\u0aff":
            return "Gujarati"
    return "English"
