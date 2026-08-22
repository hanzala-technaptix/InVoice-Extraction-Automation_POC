from pathlib import Path

from app.core.ai import AIConfigurationError, AIExtractionError
from app.modules.invoice.extractor import InvoiceExtractionError, extract_invoice_from_pdf
from app.modules.invoice.repository import (
    RepositoryError,
    get_all_invoices,
    get_invoice_by_id,
    init_db,
    save_invoice,
)
from app.modules.invoice.schemas import (
    ApprovedInvoiceRequest,
    ApprovedInvoiceResponse,
    ExtractedInvoiceResponse,
)
from app.modules.invoice.validator import ValidationResult, validate_invoice


class InvoiceServiceError(Exception):
    """Base exception for invoice service failures."""


class InvoiceValidationError(InvoiceServiceError):
    """Raised when approved invoice data fails validation."""

    def __init__(self, errors: list[str], warnings: list[str] | None = None):
        self.errors = errors
        self.warnings = warnings or []
        message = "; ".join(errors) if errors else "Invoice validation failed."
        super().__init__(message)


class InvoicePersistenceError(InvoiceServiceError):
    """Raised when saving or loading invoice data fails."""


def initialize() -> None:
    """Initialize the invoice database."""
    init_db()


def extract_invoice(file_path: str | Path) -> ExtractedInvoiceResponse:
    """
    Extract invoice data from a PDF using OCR and AI.

    Args:
        file_path: Path to an invoice PDF file.

    Returns:
        Extracted invoice data for user review.

    Raises:
        InvoiceExtractionError: If OCR extraction fails.
        InvoiceServiceError: If AI extraction is not configured or fails.
    """
    try:
        return extract_invoice_from_pdf(file_path)
    except (AIConfigurationError, AIExtractionError) as exc:
        raise InvoiceServiceError(str(exc)) from exc


def validate_extracted_invoice(
    invoice: ExtractedInvoiceResponse,
) -> ValidationResult:
    """Validate extracted invoice data before or after user review."""
    return validate_invoice(invoice)


def validate_approved_invoice(
    invoice: ApprovedInvoiceRequest,
) -> ValidationResult:
    """Validate user-approved invoice data before saving."""
    return validate_invoice(invoice)


def approve_and_save_invoice(
    invoice: ApprovedInvoiceRequest,
) -> ApprovedInvoiceResponse:
    """
    Validate and persist an approved invoice.

    Args:
        invoice: User-reviewed invoice data ready for approval.

    Returns:
        Saved invoice with database IDs.

    Raises:
        InvoiceValidationError: If validation errors are present.
        InvoicePersistenceError: If the database save fails.
    """
    validation = validate_invoice(invoice)
    if not validation.is_valid:
        raise InvoiceValidationError(validation.errors, validation.warnings)

    try:
        return save_invoice(invoice)
    except RepositoryError as exc:
        raise InvoicePersistenceError(str(exc)) from exc


def list_saved_invoices() -> list[ApprovedInvoiceResponse]:
    """
    Retrieve all saved invoices.

    Raises:
        InvoicePersistenceError: If loading invoices fails.
    """
    try:
        return get_all_invoices()
    except RepositoryError as exc:
        raise InvoicePersistenceError(str(exc)) from exc


def get_saved_invoice(invoice_id: int) -> ApprovedInvoiceResponse | None:
    """
    Retrieve one saved invoice by ID.

    Raises:
        InvoicePersistenceError: If loading the invoice fails.
    """
    try:
        return get_invoice_by_id(invoice_id)
    except RepositoryError as exc:
        raise InvoicePersistenceError(str(exc)) from exc
