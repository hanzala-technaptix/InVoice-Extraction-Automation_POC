"""
Gmail IMAP credentials for the Invoice Automation POC.

Configure in .env (no OAuth client ID required):
    GMAIL_EMAIL=your.email@gmail.com
    GMAIL_APP_PASSWORD=your16digitapppassword
"""

from app.config import get_settings


class GmailIMAPError(Exception):
    """Raised when Gmail IMAP credentials are missing or invalid."""


def get_imap_credentials() -> tuple[str, str]:
    """
    Return Gmail email and app password from settings.

    Raises:
        GmailIMAPError: If either value is not configured.
    """
    settings = get_settings()
    email = settings.gmail_email.strip()
    app_password = settings.gmail_app_password.strip().replace(" ", "")

    if not email:
        raise GmailIMAPError("GMAIL_EMAIL is not configured in .env.")
    if not app_password:
        raise GmailIMAPError("GMAIL_APP_PASSWORD is not configured in .env.")

    return email, app_password


def is_configured() -> bool:
    """Return True when Gmail email and app password are set."""
    try:
        get_imap_credentials()
        return True
    except GmailIMAPError:
        return False
