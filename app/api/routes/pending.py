from fastapi import APIRouter, HTTPException, Query, status

from app.modules.pending.models import PendingInvoiceStatus
from app.modules.pending.repository import (
    PendingRepositoryError,
    delete_pending_invoice,
    get_pending_invoice_by_id,
    list_pending_invoices,
)
from app.modules.pending.schemas import PendingInvoiceDetail, PendingInvoiceSummary

router = APIRouter(prefix="/pending-invoices", tags=["pending-invoices"])


@router.get("", response_model=list[PendingInvoiceSummary])
def get_pending_invoices(
    invoice_status: PendingInvoiceStatus | None = Query(
        default=PendingInvoiceStatus.PENDING_REVIEW,
        alias="status",
        description="Filter by status. Omit to return all.",
    ),
) -> list[PendingInvoiceSummary]:
    """List invoices waiting in the pending review inbox."""
    try:
        return list_pending_invoices(status=invoice_status)
    except PendingRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get("/{pending_id}", response_model=PendingInvoiceDetail)
def get_pending_invoice(pending_id: int) -> PendingInvoiceDetail:
    """
    Load one pending invoice with full extracted data for Review/Edit.

    Returns extracted_data (vendor, dates, amounts, line items), pdf_path,
    filename, and gmail_source metadata.
    """
    try:
        pending = get_pending_invoice_by_id(pending_id)
    except PendingRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    if pending is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pending invoice {pending_id} not found.",
        )

    return pending


@router.delete("/{pending_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_pending_invoice(pending_id: int) -> None:
    """Delete a pending invoice from the review queue."""
    try:
        delete_pending_invoice(pending_id)
    except PendingRepositoryError as exc:
        message = str(exc)
        if "not found" in message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc
        if "already saved" in message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message,
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
        ) from exc
