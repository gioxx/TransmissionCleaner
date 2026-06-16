import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

from app.config import settings
from app.models import CleanupResult

logger = logging.getLogger(__name__)


def _should_notify(result: CleanupResult) -> bool:
    if settings.notify_always:
        return True
    return result.deleted_count > 0 or result.error_count > 0


async def send_telegram(result: CleanupResult) -> None:
    if not settings.telegram_enabled or not settings.telegram_bot_token:
        return
    if not _should_notify(result):
        return
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": result.to_telegram(),
        "parse_mode": "HTML",
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
        logger.info("Telegram notification sent")
    except Exception as e:
        logger.error("Telegram notification failed: %s", e)


def send_resend(result: CleanupResult) -> None:
    if not settings.resend_enabled or not settings.resend_api_key:
        return
    if not _should_notify(result):
        return
    try:
        import resend
        resend.api_key = settings.resend_api_key
        params: resend.Emails.SendParams = {
            "from": settings.resend_from,
            "to": [settings.resend_to],
            "subject": f"Transmission Cleaner — {result.deleted_count} removed",
            "text": result.to_email_body(),
        }
        resend.Emails.send(params)
        logger.info("Resend notification sent")
    except Exception as e:
        logger.error("Resend notification failed: %s", e)


def send_smtp(result: CleanupResult) -> None:
    if not settings.smtp_enabled:
        return
    if not _should_notify(result):
        return
    msg = MIMEMultipart()
    msg["Subject"] = f"Transmission Cleaner — {result.deleted_count} removed"
    msg["From"] = settings.smtp_from
    msg["To"] = settings.smtp_to
    msg.attach(MIMEText(result.to_email_body(), "plain", "utf-8"))
    try:
        if settings.smtp_tls:
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, context=ctx) as s:
                if settings.smtp_user:
                    s.login(settings.smtp_user, settings.smtp_password)
                s.send_message(msg)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as s:
                s.ehlo()
                try:
                    s.starttls()
                except smtplib.SMTPException:
                    pass
                if settings.smtp_user:
                    s.login(settings.smtp_user, settings.smtp_password)
                s.send_message(msg)
        logger.info("SMTP notification sent")
    except Exception as e:
        logger.error("SMTP notification failed: %s", e)


async def notify_all(result: CleanupResult) -> None:
    await send_telegram(result)
    send_resend(result)
    send_smtp(result)
