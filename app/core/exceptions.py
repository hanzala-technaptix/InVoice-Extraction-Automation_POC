"""Shared exception hierarchy for the Invoice Automation POC."""


class InvoiceAutomationError(Exception):
    """Base exception for invoice automation errors."""


class OCRError(InvoiceAutomationError):
    """Raised when OCR processing fails."""


class UnsupportedFileTypeError(OCRError):
    """Raised when a file type is not supported for OCR."""


class AIConfigurationError(InvoiceAutomationError):
    """Raised when OpenAI is not configured correctly."""


class AIExtractionError(InvoiceAutomationError):
    """Raised when AI invoice extraction fails."""


class InvoiceExtractionError(InvoiceAutomationError):
    """Raised when PDF invoice extraction fails before or during AI processing."""


class RepositoryError(InvoiceAutomationError):
    """Raised when a database repository operation fails."""


class InvoiceServiceError(InvoiceAutomationError):
    """Base exception for invoice service-layer failures."""


class InvoiceValidationError(InvoiceServiceError):
    """Raised when invoice data fails business validation."""

    def __init__(self, errors: list[str], warnings: list[str] | None = None):
        self.errors = errors
        self.warnings = warnings or []
        message = "; ".join(errors) if errors else "Invoice validation failed."
        super().__init__(message)


class InvoicePersistenceError(InvoiceServiceError):
    """Raised when saving or loading invoice data fails at the service layer."""
