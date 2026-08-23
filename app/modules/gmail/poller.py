"""
Background Gmail poller for the Invoice Automation POC.

Finds PDF attachments, runs the existing extraction pipeline, and queues
results in pending_invoices for human review.
"""

from dataclasses import dataclass, field

from app.core.exceptions import InvoiceAutomationError, UnsupportedFileTypeError
from app.modules.gmail.fetcher import (
    GmailFetchError,
    GmailMessageSummary,
    GmailPdfAttachment,
    download_attachment,
    is_imap_available,
    list_invoice_messages,
)
from app.modules.invoice.extractor import InvoiceExtractionError
from app.modules.invoice.service import InvoiceServiceError, extract_invoice
from app.modules.pending.repository import (
    PendingInvoiceDuplicateError,
    PendingRepositoryError,
    create_failed_pending_invoice,
    create_pending_invoice,
    pending_invoice_exists,
)
from app.modules.pending.schemas import PendingInvoiceCreate, PendingInvoiceFailureCreate
from app.utils.file_handler import save_pdf_bytes


@dataclass
class GmailPollResult:
    """Summary of one Gmail inbox poll run."""

    configured: bool
    processed: int = 0
    queued: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


def poll_gmail_inbox(max_results: int = 20) -> GmailPollResult:
    """
    Poll Gmail for PDF attachments not yet in the pending review queue.

    For each new attachment:
      download PDF → save_pdf_bytes() → extract_invoice() → pending queue

    Already-queued attachments are skipped (dedup by message_id + attachment_id).
    Extraction failures are recorded as failed pending rows. Errors on one
    attachment do not stop processing of the rest or the background loop.
    """
    if not is_imap_available():
        return GmailPollResult(configured=False)

    result = GmailPollResult(configured=True)

    try:
        messages = list_invoice_messages(max_results=max_results)
    except GmailFetchError as exc:
        result.errors.append(str(exc))
        return result

    for message in messages:
        for attachment in message.pdf_attachments:
            result.processed += 1
            _process_attachment(message, attachment, result)

    return result


def _process_attachment(
    message: GmailMessageSummary,
    attachment: GmailPdfAttachment,
    result: GmailPollResult,
) -> None:
    if pending_invoice_exists(message.message_id, attachment.attachment_id):
        result.skipped += 1
        return

    pdf_path = ""
    try:
        content = download_attachment(message.message_id, attachment.attachment_id)
        pdf_path = str(save_pdf_bytes(content, attachment.filename))
    except (GmailFetchError, UnsupportedFileTypeError, InvoiceAutomationError) as exc:
        _record_failure(message, attachment, pdf_path, str(exc), result)
        return

    try:
        invoice = extract_invoice(pdf_path)
    except (InvoiceExtractionError, InvoiceServiceError) as exc:
        _record_failure(message, attachment, pdf_path, str(exc), result)
        return

    try:
        create_pending_invoice(
            PendingInvoiceCreate(
                gmail_message_id=message.message_id,
                gmail_attachment_id=attachment.attachment_id,
                pdf_path=pdf_path,
                extracted_data=invoice,
                sender_email=message.sender,
                subject=message.subject,
                filename=attachment.filename,
                received_at=message.received_at,
            )
        )
        result.queued += 1
    except PendingInvoiceDuplicateError:
        result.skipped += 1
    except PendingRepositoryError as exc:
        result.failed += 1
        result.errors.append(f"Failed to queue {attachment.filename}: {exc}")
    except Exception as exc:
        _record_failure(message, attachment, pdf_path, str(exc), result)


def _record_failure(
    message: GmailMessageSummary,
    attachment: GmailPdfAttachment,
    pdf_path: str,
    error_message: str,
    result: GmailPollResult,
) -> None:
    try:
        create_failed_pending_invoice(
            PendingInvoiceFailureCreate(
                gmail_message_id=message.message_id,
                gmail_attachment_id=attachment.attachment_id,
                pdf_path=pdf_path,
                sender_email=message.sender,
                subject=message.subject,
                filename=attachment.filename,
                received_at=message.received_at,
                error_message=error_message,
            )
        )
        result.failed += 1
    except PendingInvoiceDuplicateError:
        result.skipped += 1
    except Exception as exc:
        result.failed += 1
        result.errors.append(
            f"Failed to record error for {attachment.filename}: {exc}"
        )
