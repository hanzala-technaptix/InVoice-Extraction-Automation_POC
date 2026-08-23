"""
Gmail fetcher via IMAP + app password (POC).

Uses imap.gmail.com with GMAIL_EMAIL and GMAIL_APP_PASSWORD from .env.
"""

import email
import imaplib
from dataclasses import dataclass
from datetime import datetime
from email.header import decode_header
from email.utils import parsedate_to_datetime

from app.config import get_settings
from app.modules.gmail.imap_auth import GmailIMAPError, get_imap_credentials

IMAP_HOST = "imap.gmail.com"
DEFAULT_IMAP_QUERY = 'has:attachment filename:pdf'
DEFAULT_MAX_RESULTS = 20


class GmailFetchError(Exception):
    """Raised when Gmail search or attachment download fails."""


@dataclass
class GmailPdfAttachment:
    """A PDF attachment found on a Gmail message."""

    message_id: str
    attachment_id: str
    filename: str


@dataclass
class GmailMessageSummary:
    """Summary of a Gmail message that has one or more PDF attachments."""

    message_id: str
    subject: str
    sender: str
    received_at: datetime | None
    pdf_attachments: list[GmailPdfAttachment]


def list_invoice_messages(max_results: int = DEFAULT_MAX_RESULTS) -> list[GmailMessageSummary]:
    """
    Search Gmail inbox for messages with PDF attachments.

    Raises:
        GmailFetchError: If IMAP is not configured or the search fails.
    """
    mail = _open_imap()
    try:
        uids = _search_message_uids(mail, max_results)
        summaries: list[GmailMessageSummary] = []

        for uid in uids:
            summary = _build_message_summary(mail, uid)
            if summary.pdf_attachments:
                summaries.append(summary)

        return summaries
    finally:
        _close_imap(mail)


def get_message_pdf_attachments(message_id: str) -> list[GmailPdfAttachment]:
    """
    Return PDF attachments for one Gmail message.

    Raises:
        GmailFetchError: If the message cannot be loaded.
    """
    mail = _open_imap()
    try:
        return _build_message_summary(mail, message_id).pdf_attachments
    finally:
        _close_imap(mail)


def download_attachment(message_id: str, attachment_id: str) -> bytes:
    """
    Download raw PDF attachment bytes from Gmail via IMAP.

    attachment_id is the MIME part index returned when listing attachments.

    Raises:
        GmailFetchError: If the download fails or payload is empty.
    """
    mail = _open_imap()
    try:
        message = _fetch_message(mail, message_id)
        part_index = int(attachment_id)

        for index, part in enumerate(message.walk()):
            if index != part_index:
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                raise GmailFetchError("Attachment payload is empty.")
            return payload

        raise GmailFetchError(
            f"PDF attachment {attachment_id} was not found on message {message_id}."
        )
    finally:
        _close_imap(mail)


def verify_imap_connection() -> bool:
    """Return True if IMAP login succeeds with configured credentials."""
    if not is_imap_available():
        return False

    mail = None
    try:
        mail = _open_imap()
        return True
    except GmailFetchError:
        return False
    finally:
        if mail is not None:
            _close_imap(mail)


def is_imap_available() -> bool:
    from app.modules.gmail.imap_auth import is_configured

    return is_configured()


def _open_imap() -> imaplib.IMAP4_SSL:
    try:
        email_address, app_password = get_imap_credentials()
    except GmailIMAPError as exc:
        raise GmailFetchError(str(exc)) from exc

    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST)
        mail.login(email_address, app_password)
        mail.select("INBOX")
    except imaplib.IMAP4.error as exc:
        raise GmailFetchError(
            "Gmail IMAP login failed. Check GMAIL_EMAIL and GMAIL_APP_PASSWORD in .env."
        ) from exc
    except OSError as exc:
        raise GmailFetchError(f"Could not connect to Gmail IMAP: {exc}") from exc

    return mail


def _close_imap(mail: imaplib.IMAP4_SSL) -> None:
    try:
        mail.close()
    except imaplib.IMAP4.error:
        pass
    try:
        mail.logout()
    except imaplib.IMAP4.error:
        pass


def _search_message_uids(mail: imaplib.IMAP4_SSL, max_results: int) -> list[str]:
    query = get_settings().gmail_query.strip() or DEFAULT_IMAP_QUERY

    try:
        status, data = mail.uid("search", None, "X-GM-RAW", query)
    except imaplib.IMAP4.error:
        status, data = mail.uid("search", None, "ALL")

    if status != "OK" or not data or not data[0]:
        return []

    uids = data[0].split()
    uids.reverse()
    return [uid.decode() for uid in uids[:max_results]]


def _build_message_summary(mail: imaplib.IMAP4_SSL, message_id: str) -> GmailMessageSummary:
    message = _fetch_message(mail, message_id)
    pdf_attachments = _find_pdf_attachments(message, message_id)

    return GmailMessageSummary(
        message_id=message_id,
        subject=_decode_header_value(message.get("Subject")) or "(no subject)",
        sender=_decode_header_value(message.get("From")) or "(unknown sender)",
        received_at=_parse_received_at(message.get("Date")),
        pdf_attachments=pdf_attachments,
    )


def _fetch_message(mail: imaplib.IMAP4_SSL, message_id: str) -> email.message.Message:
    status, data = mail.uid("fetch", message_id, "(RFC822)")
    if status != "OK" or not data or not data[0]:
        raise GmailFetchError(f"Failed to load Gmail message {message_id}.")

    raw_message = data[0][1]
    if not isinstance(raw_message, (bytes, bytearray)):
        raise GmailFetchError(f"Unexpected Gmail message payload for {message_id}.")

    return email.message_from_bytes(raw_message)


def _find_pdf_attachments(message: email.message.Message, message_id: str) -> list[GmailPdfAttachment]:
    attachments: list[GmailPdfAttachment] = []

    for index, part in enumerate(message.walk()):
        if part.get_content_maintype() == "multipart":
            continue

        filename = part.get_filename()
        if not filename:
            continue

        decoded_filename = _decode_header_value(filename)
        if not decoded_filename.lower().endswith(".pdf"):
            continue

        attachments.append(
            GmailPdfAttachment(
                message_id=message_id,
                attachment_id=str(index),
                filename=decoded_filename,
            )
        )

    return attachments


def _decode_header_value(value: str | None) -> str:
    if not value:
        return ""

    parts: list[str] = []
    for fragment, encoding in decode_header(value):
        if isinstance(fragment, bytes):
            parts.append(fragment.decode(encoding or "utf-8", errors="replace"))
        else:
            parts.append(fragment)
    return "".join(parts).strip()


def _parse_received_at(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return None

    if parsed.tzinfo is not None:
        return parsed.astimezone().replace(tzinfo=None)
    return parsed
