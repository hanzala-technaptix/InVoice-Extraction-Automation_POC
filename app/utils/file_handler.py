import re
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import UploadFile

from app.config import get_settings
from app.core.exceptions import InvoiceAutomationError, UnsupportedFileTypeError

PDF_EXTENSION = ".pdf"
PDF_MAGIC_BYTES = b"%PDF-"
SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")

SaveSource = Literal["manual", "gmail", "invoices"]


async def save_uploaded_pdf(file: UploadFile) -> Path:
    """Validate and save an uploaded PDF under data/uploads/invoices/."""
    content = await file.read()
    return save_pdf_bytes(content, file.filename or "invoice.pdf", source="invoices")


def save_pdf_bytes(
    content: bytes,
    filename: str,
    *,
    source: SaveSource = "gmail",
) -> Path:
    """
    Validate and save PDF bytes under data/uploads/{source}/.

    Layout:
      invoices/ — raw PDF uploaded from Process Invoice ({sanitized_name}.pdf)
      manual/   — extracted manual upload (extract_{sanitized_name}.pdf)
      gmail/    — extracted Gmail ingress ({uuid}_{sanitized_name}.pdf)

    Args:
        content: Raw PDF file bytes.
        filename: Original filename used for validation and sanitization.
        source: "invoices", "manual", or "gmail".

    Returns:
        Path to the saved PDF on disk.
    """
    _validate_pdf_filename(filename)
    _validate_pdf_content(content)

    upload_dir = Path(get_settings().upload_dir) / source

    if source == "manual":
        saved_name = _generate_extract_filename(filename)
    elif source == "gmail":
        saved_name = _generate_unique_filename(filename)
    else:
        saved_name = _sanitize_filename(filename or "invoice.pdf")

    saved_path = upload_dir / saved_name
    saved_path.write_bytes(content)

    return saved_path


def _validate_pdf_filename(filename: str | None) -> None:
    if not filename or not filename.lower().endswith(PDF_EXTENSION):
        raise UnsupportedFileTypeError("Only PDF files are supported.")


def _validate_pdf_content(content: bytes) -> None:
    if not content:
        raise InvoiceAutomationError("Uploaded file is empty.")

    if not content.startswith(PDF_MAGIC_BYTES):
        raise UnsupportedFileTypeError("File content is not a valid PDF.")


def _sanitize_filename(filename: str) -> str:
    """Return a safe filename without directory components."""
    name = Path(filename).name.strip()
    if not name:
        return "invoice.pdf"

    stem = Path(name).stem
    cleaned_stem = SAFE_FILENAME_PATTERN.sub("_", stem).strip("._") or "invoice"
    return f"{cleaned_stem}.pdf"


def _generate_extract_filename(filename: str | None) -> str:
    """Manual upload / demo extract — no UUID, prefixed with extract_."""
    safe_name = _sanitize_filename(filename or "invoice.pdf")
    return f"extract_{safe_name}"


def _generate_unique_filename(filename: str | None) -> str:
    """Gmail ingress — UUID prefix so each poll/download is a distinct file."""
    safe_name = _sanitize_filename(filename or "invoice.pdf")
    return f"{uuid4()}_{safe_name}"
