from pathlib import Path

from app.core.ai import extract_invoice_from_text
from app.core.ocr import OCRError, extract_text_from_file
from app.modules.invoice.schemas import ExtractedInvoiceResponse


class InvoiceExtractionError(Exception):
    """Raised when invoice extraction from a PDF fails."""


def extract_invoice_from_pdf(file_path: str | Path) -> ExtractedInvoiceResponse:
    """
    Extract structured invoice data from a PDF file.

    Orchestrates OCR text extraction followed by AI field extraction.

    Args:
        file_path: Path to an invoice PDF file.

    Returns:
        Structured invoice data extracted from the PDF.

    Raises:
        InvoiceExtractionError: If OCR fails or produces no usable text.
        AIConfigurationError: If OpenAI is not configured (from ai module).
        AIExtractionError: If AI extraction fails (from ai module).
    """
    path = Path(file_path)

    try:
        invoice_text = extract_text_from_file(path)
    except FileNotFoundError as exc:
        raise InvoiceExtractionError(str(exc)) from exc
    except OCRError as exc:
        raise InvoiceExtractionError(f"OCR failed for PDF: {path}") from exc

    if not invoice_text.strip():
        raise InvoiceExtractionError(
            f"OCR produced no readable text from PDF: {path}"
        )

    return extract_invoice_from_text(invoice_text)
