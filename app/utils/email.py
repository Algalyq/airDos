import json
import logging
import urllib.request
import urllib.error

from fastapi import BackgroundTasks

from app.core.config import get_settings

logger = logging.getLogger("airdos.email")

settings = get_settings()

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Код подтверждения airDos</title>
</head>
<body>
    <p>Здравствуйте!</p>
    <p>Ваш код подтверждения для <strong>airDos</strong>: <strong style="font-size: 24px;">{code}</strong></p>
    <p>Срок действия — 5 минут.</p>
</body>
</html>
"""


def _send_email(to_email: str, code: str) -> None:
    logger.info(">>> [airDos] Verification code for %s: %s", to_email, code)

    resend_api_key = settings.RESEND_API_KEY
    mail_from = settings.MAIL_FROM

    if not resend_api_key:
        logger.warning("RESEND_API_KEY not set, skipping email send")
        return
    if not mail_from:
        logger.warning("MAIL_FROM not set, skipping email send")
        return

    payload = json.dumps({
        "from": mail_from,
        "to": [to_email],
        "subject": "Код подтверждения airDos",
        "html": HTML_TEMPLATE.format(code=code),
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {resend_api_key}",
            "Content-Type": "application/json",
            "User-Agent": "airDos/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode()
            logger.info("Email sent successfully to %s: %s", to_email, body)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        logger.error("Resend API error %s: %s", e.code, error_body)
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, e)


def send_verification_code(
    background_tasks: BackgroundTasks,
    email: str,
    code: str,
) -> None:
    background_tasks.add_task(_send_email, email, code)
