import json

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.modules.invoice.repository import _get_session
from app.modules.invoice.schemas import ExtractedInvoiceResponse
from app.modules.pending.models import PendingInvoice, PendingInvoiceStatus
from app.modules.pending.schemas import (
    GmailSourceInfo,
    PendingInvoiceCreate,
    PendingInvoiceDetail,
    PendingInvoiceFailureCreate,
    PendingInvoiceSummary,
)


class PendingRepositoryError(Exception):
    """Raised when a pending-invoice database operation fails."""


class PendingInvoiceDuplicateError(PendingRepositoryError):
    """Raised when the same Gmail attachment was already queued."""


def pending_invoice_exists(gmail_message_id: str, gmail_attachment_id: str) -> bool:
    """Return True if this Gmail attachment is already in the pending queue."""
    session = _get_session()
    try:
        existing = session.scalars(
            select(PendingInvoice.id).where(
                PendingInvoice.gmail_message_id == gmail_message_id,
                PendingInvoice.gmail_attachment_id == gmail_attachment_id,
            )
        ).first()
        return existing is not None
    except SQLAlchemyError as exc:
        session.rollback()
        raise PendingRepositoryError("Failed to check pending invoice.") from exc
    finally:
        session.close()


def create_pending_invoice(data: PendingInvoiceCreate) -> PendingInvoiceDetail:
    """
    Queue an extracted invoice for user review.

    Stores the full ExtractedInvoiceResponse JSON so the frontend can
    populate the Review/Edit form without re-running extraction.
    """
    session = _get_session()
    try:
        pending = PendingInvoice(
            status=PendingInvoiceStatus.PENDING_REVIEW,
            source=data.source,
            gmail_message_id=data.gmail_message_id,
            gmail_attachment_id=data.gmail_attachment_id,
            pdf_path=data.pdf_path,
            extracted_json=data.extracted_data.model_dump_json(),
            vendor_name=data.extracted_data.vendor_name,
            invoice_number=data.extracted_data.invoice_number,
            sender_email=data.sender_email,
            subject=data.subject,
            filename=data.filename,
            received_at=data.received_at,
        )
        session.add(pending)
        session.commit()
        session.refresh(pending)
        return _to_pending_detail(pending)
    except IntegrityError as exc:
        session.rollback()
        raise PendingInvoiceDuplicateError(
            "This Gmail attachment is already in the pending review queue."
        ) from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise PendingRepositoryError("Failed to queue pending invoice.") from exc
    finally:
        session.close()


def create_failed_pending_invoice(
    data: PendingInvoiceFailureCreate,
) -> PendingInvoiceDetail:
    """Record a Gmail attachment that could not be extracted."""
    session = _get_session()
    try:
        pending = PendingInvoice(
            status=PendingInvoiceStatus.FAILED,
            source=data.source,
            gmail_message_id=data.gmail_message_id,
            gmail_attachment_id=data.gmail_attachment_id,
            pdf_path=data.pdf_path,
            extracted_json=json.dumps({}),
            sender_email=data.sender_email,
            subject=data.subject,
            filename=data.filename,
            received_at=data.received_at,
            error_message=data.error_message,
        )
        session.add(pending)
        session.commit()
        session.refresh(pending)
        return _to_pending_detail(pending)
    except IntegrityError as exc:
        session.rollback()
        raise PendingInvoiceDuplicateError(
            "This Gmail attachment is already in the pending review queue."
        ) from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise PendingRepositoryError("Failed to record failed pending invoice.") from exc
    finally:
        session.close()


def list_pending_invoices(
    *,
    status: PendingInvoiceStatus | None = PendingInvoiceStatus.PENDING_REVIEW,
) -> list[PendingInvoiceSummary]:
    """
    List pending invoices for the web app inbox.

    Args:
        status: Filter by status. Pass None to return all statuses.
    """
    session = _get_session()
    try:
        query = select(PendingInvoice).order_by(PendingInvoice.created_at.desc())
        if status is not None:
            query = query.where(PendingInvoice.status == status)

        rows = session.scalars(query).all()
        return [_to_pending_summary(row) for row in rows]
    except SQLAlchemyError as exc:
        session.rollback()
        raise PendingRepositoryError("Failed to list pending invoices.") from exc
    finally:
        session.close()


def get_pending_invoice_by_id(pending_id: int) -> PendingInvoiceDetail | None:
    """Load one pending invoice with full extracted data for review."""
    session = _get_session()
    try:
        pending = session.get(PendingInvoice, pending_id)
        if pending is None:
            return None
        return _to_pending_detail(pending)
    except SQLAlchemyError as exc:
        session.rollback()
        raise PendingRepositoryError("Failed to load pending invoice.") from exc
    finally:
        session.close()


def mark_pending_invoice_saved(
    pending_id: int,
    approved_invoice_id: int,
) -> PendingInvoiceDetail:
    """Mark a pending invoice as saved after user approval."""
    session = _get_session()
    try:
        pending = session.get(PendingInvoice, pending_id)
        if pending is None:
            raise PendingRepositoryError(f"Pending invoice {pending_id} not found.")

        pending.status = PendingInvoiceStatus.SAVED
        pending.approved_invoice_id = approved_invoice_id
        session.commit()
        session.refresh(pending)
        return _to_pending_detail(pending)
    except PendingRepositoryError:
        session.rollback()
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        raise PendingRepositoryError("Failed to update pending invoice.") from exc
    finally:
        session.close()


def _to_pending_summary(pending: PendingInvoice) -> PendingInvoiceSummary:
    return PendingInvoiceSummary(
        id=pending.id,
        status=PendingInvoiceStatus(pending.status),
        source=pending.source,
        vendor_name=pending.vendor_name,
        invoice_number=pending.invoice_number,
        sender_email=pending.sender_email,
        subject=pending.subject,
        filename=pending.filename,
        received_at=pending.received_at,
        created_at=pending.created_at,
        error_message=pending.error_message,
    )


def _to_gmail_source(pending: PendingInvoice) -> GmailSourceInfo:
    return GmailSourceInfo(
        message_id=pending.gmail_message_id,
        attachment_id=pending.gmail_attachment_id,
        sender=pending.sender_email,
        subject=pending.subject,
        filename=pending.filename,
        received_at=pending.received_at,
    )


def _to_pending_detail(pending: PendingInvoice) -> PendingInvoiceDetail:
    extracted_data = ExtractedInvoiceResponse.model_validate_json(pending.extracted_json)
    return PendingInvoiceDetail(
        id=pending.id,
        status=PendingInvoiceStatus(pending.status),
        source=pending.source,
        vendor_name=pending.vendor_name,
        invoice_number=pending.invoice_number,
        sender_email=pending.sender_email,
        subject=pending.subject,
        filename=pending.filename,
        received_at=pending.received_at,
        created_at=pending.created_at,
        error_message=pending.error_message,
        pdf_path=pending.pdf_path,
        extracted_data=extracted_data,
        gmail_source=_to_gmail_source(pending),
        approved_invoice_id=pending.approved_invoice_id,
    )
