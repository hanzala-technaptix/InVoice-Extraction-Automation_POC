import re
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import get_settings
from app.core.exceptions import InvoiceAutomationError, UnsupportedFileTypeError

PDF_EXTENSION = ".pdf"
PDF_MAGIC_BYTES = b"%PDF-"
SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


async def save_uploaded_pdf(file: UploadFile) -> Path:
    """
    Validate and save an uploaded PDF file.

    Args:
        file: Uploaded PDF file from the API layer.

    Returns:
        Path to the saved PDF on disk.

    Raises:
        UnsupportedFileTypeError: If the file is not a supported PDF.
        InvoiceAutomationError: If the uploaded file is empty.
    """
    _validate_pdf_filename(file.filename)

    content = await file.read()
    _validate_pdf_content(content)

    upload_dir = Path(get_settings().upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    saved_path = upload_dir / _generate_unique_filename(file.filename)
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


def _generate_unique_filename(filename: str | None) -> str:
    safe_name = _sanitize_filename(filename or "invoice.pdf")
    return f"{uuid4()}_{safe_name}"
