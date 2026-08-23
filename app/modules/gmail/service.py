"""
Gmail service layer for the Invoice Automation POC.

Orchestrates:
  Gmail IMAP fetcher → save_pdf_bytes() → existing extract_invoice() pipeline

Uses GMAIL_EMAIL + GMAIL_APP_PASSWORD from .env (no OAuth).
"""

from dataclasses import dataclass
from pathlib import Path

from app.core.exceptions import InvoiceAutomationError, UnsupportedFileTypeError
from app.modules.gmail.fetcher import (
    GmailFetchError,
    GmailMessageSummary,
    GmailPdfAttachment,
    download_attachment,
    get_message_pdf_attachments,
    list_invoice_messages,
    verify_imap_connection,
)
from app.modules.gmail.imap_auth import is_configured
from app.modules.invoice.extractor import InvoiceExtractionError
from app.modules.invoice.schemas import ExtractedInvoiceResponse
from app.modules.invoice.service import InvoiceServiceError, extract_invoice
from app.utils.file_handler import save_pdf_bytes


class GmailServiceError(Exception):
    """Raised when Gmail invoice ingestion fails."""


@dataclass
class GmailExtractResult:
    """Invoice data extracted from a Gmail PDF attachment."""

    invoice: ExtractedInvoiceResponse
    message_id: str
    attachment_id: str
    filename: str
    pdf_path: Path


def gmail_connection_status() -> dict[str, bool | str | None]:
    """Return Gmail IMAP configuration and connection status."""
    configured = is_configured()
    connected = verify_imap_connection() if configured else False
    return {
        "configured": configured,
        "connected": connected,
    }


def list_gmail_invoice_messages(
    max_results: int = 20,
) -> list[GmailMessageSummary]:
    """
    List Gmail messages that contain PDF attachments.

    Raises:
        GmailServiceError: If Gmail is not configured or search fails.
    """
    try:
        return list_invoice_messages(max_results=max_results)
    except GmailFetchError as exc:
        raise GmailServiceError(str(exc)) from exc


def list_gmail_pdf_attachments(message_id: str) -> list[GmailPdfAttachment]:
    """
    List PDF attachments for one Gmail message.

    Raises:
        GmailServiceError: If the message cannot be loaded.
    """
    try:
        return get_message_pdf_attachments(message_id)
    except GmailFetchError as exc:
        raise GmailServiceError(str(exc)) from exc


def extract_invoice_from_gmail_attachment(
    message_id: str,
    attachment_id: str,
) -> GmailExtractResult:
    """
    Download a Gmail PDF attachment, save it once, and run the existing
    invoice extraction pipeline.

    Raises:
        GmailServiceError: If download, save, or extraction fails.
    """
    attachment = _find_pdf_attachment(message_id, attachment_id)
    if attachment is None:
        raise GmailServiceError(
            f"PDF attachment {attachment_id} was not found on message {message_id}."
        )

    try:
        content = download_attachment(message_id, attachment_id)
    except GmailFetchError as exc:
        raise GmailServiceError(str(exc)) from exc

    try:
        pdf_path = save_pdf_bytes(content, attachment.filename)
    except (UnsupportedFileTypeError, InvoiceAutomationError) as exc:
        raise GmailServiceError(str(exc)) from exc

    try:
        invoice = extract_invoice(pdf_path)
    except InvoiceExtractionError as exc:
        raise GmailServiceError(str(exc)) from exc
    except InvoiceServiceError as exc:
        raise GmailServiceError(str(exc)) from exc

    return GmailExtractResult(
        invoice=invoice,
        message_id=message_id,
        attachment_id=attachment_id,
        filename=attachment.filename,
        pdf_path=pdf_path,
    )


def _find_pdf_attachment(
    message_id: str,
    attachment_id: str,
) -> GmailPdfAttachment | None:
    try:
        attachments = get_message_pdf_attachments(message_id)
    except GmailFetchError as exc:
        raise GmailServiceError(str(exc)) from exc

    for attachment in attachments:
        if attachment.attachment_id == attachment_id:
            return attachment
    return None
