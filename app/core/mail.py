"""E-Mail-Versand via SMTP mit STARTTLS.

Wenn keine SMTP-Konfiguration gesetzt ist (SMTP_HOST leer), wird die Nachricht
nur geloggt und kein Netzwerkzugriff durchgeführt.
"""
import logging
import smtplib
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_mail(to: str, subject: str, body: str) -> None:
    if not settings.SMTP_HOST:
        logger.info(
            "SMTP nicht konfiguriert – E-Mail wird nur geloggt. An: %s | Betreff: %s",
            to,
            subject,
        )
        return

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER or "noreply@dhbw.de"
    msg["To"] = to

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            smtp.ehlo()
            if smtp.has_extn("STARTTLS"):      # TLS nur wenn der Server es anbietet
                smtp.starttls()
                smtp.ehlo()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.sendmail(msg["From"], [to], msg.as_string())
        logger.info("E-Mail erfolgreich gesendet an %s | Betreff: %s", to, subject)
    except Exception:
        logger.exception("Fehler beim E-Mail-Versand an %s.", to)
