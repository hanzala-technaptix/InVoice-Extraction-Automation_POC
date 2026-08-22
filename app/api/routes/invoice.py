from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.config import get_settings
from app.modules.invoice.extractor import InvoiceExtractionError
from app.modules.invoice.schemas import (
    ApprovedInvoiceRequest,
    ApprovedInvoiceResponse,
    ExtractedInvoiceResponse,
)
from app.modules.invoice.service import (
    InvoicePersistenceError,
    InvoiceServiceError,
    InvoiceValidationError,
    approve_and_save_invoice,
    extract_invoice,
    get_saved_invoice,
    list_saved_invoices,
)

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("/extract", response_model=ExtractedInvoiceResponse)
async def extract_invoice_from_upload(
    file: UploadFile = File(..., description="PDF invoice file"),
) -> ExtractedInvoiceResponse:
    """Upload a PDF invoice and extract structured data."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    saved_path = upload_dir / f"{uuid4()}_{Path(file.filename).name}"
    saved_path.write_bytes(await file.read())

    try:
        return extract_invoice(saved_path)
    except InvoiceExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except InvoiceServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.post("/approve", response_model=ApprovedInvoiceResponse)
def approve_invoice(
    invoice: ApprovedInvoiceRequest,
) -> ApprovedInvoiceResponse:
    """Submit an approved/edited invoice and save it to SQLite."""
    try:
        return approve_and_save_invoice(invoice)
    except InvoiceValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "errors": exc.errors,
                "warnings": exc.warnings,
            },
        ) from exc
    except InvoicePersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get("", response_model=list[ApprovedInvoiceResponse])
def get_invoices() -> list[ApprovedInvoiceResponse]:
    """Get all saved invoices."""
    try:
        return list_saved_invoices()
    except InvoicePersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get("/{invoice_id}", response_model=ApprovedInvoiceResponse)
def get_invoice(invoice_id: int) -> ApprovedInvoiceResponse:
    """Get one saved invoice with its line items."""
    try:
        invoice = get_saved_invoice(invoice_id)
    except InvoicePersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found.",
        )

    return invoice
