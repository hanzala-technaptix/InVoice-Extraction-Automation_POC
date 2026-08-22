from io import BytesIO
from pathlib import Path

import pymupdf as fitz
import pytesseract
from PIL import Image
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from pytesseract import TesseractError, TesseractNotFoundError

SUPPORTED_PDF_EXTENSIONS = {".pdf"}
MIN_MEANINGFUL_ALNUM_CHARS = 20
OCR_RENDER_DPI = 200


class OCRError(Exception):
    """Raised when OCR processing fails."""


class UnsupportedFileTypeError(OCRError):
    """Raised when the file type is not supported for OCR."""


def extract_text_from_file(file_path: str | Path) -> str:
    """
    Extract raw text from an invoice PDF file.

    Uses embedded PDF text via pypdf when available, otherwise falls back to
    OCR with PyMuPDF page rendering and Tesseract.

    Args:
        file_path: Path to a PDF file.

    Returns:
        Cleaned plain-text string extracted from the PDF.

    Raises:
        FileNotFoundError: If the file does not exist.
        UnsupportedFileTypeError: If the file extension is not supported.
        OCRError: If the file is invalid or text extraction fails.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise OCRError(f"Path is not a file: {path}")

    extension = path.suffix.lower()
    if extension not in SUPPORTED_PDF_EXTENSIONS:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{extension}'. "
            f"Supported types: {', '.join(sorted(SUPPORTED_PDF_EXTENSIONS))}"
        )

    raw_text = _extract_text_from_pdf(path)
    cleaned_text = _clean_text(raw_text)
    if not cleaned_text:
        raise OCRError(f"No readable text found in PDF: {path}")
    return cleaned_text


def _extract_text_from_pdf(path: Path) -> str:
    """
    Extract text from a PDF using pypdf first, then OCR fallback if needed.
    """
    pypdf_error: OCRError | None = None

    try:
        pypdf_text = _extract_text_with_pypdf(path)
        if _is_meaningful_text(pypdf_text):
            return pypdf_text
    except OCRError as exc:
        pypdf_error = exc

    try:
        ocr_text = _extract_text_with_ocr(path)
    except OCRError as exc:
        if pypdf_error is not None:
            raise OCRError(
                f"Failed to extract text from PDF: {path}. "
                f"pypdf failed ({pypdf_error}). OCR fallback failed ({exc})."
            ) from exc
        raise

    if not _is_meaningful_text(ocr_text):
        raise OCRError(f"No readable text found in PDF: {path}")

    return ocr_text


def _extract_text_with_pypdf(path: Path) -> str:
    """Extract embedded text from all PDF pages using pypdf."""
    try:
        reader = PdfReader(str(path))
        page_texts: list[str] = []

        for page in reader.pages:
            page_text = page.extract_text() or ""
            page_texts.append(page_text)

        return "\n\n".join(page_texts)
    except PdfReadError as exc:
        raise OCRError(f"Cannot read PDF file: {path}") from exc


def _extract_text_with_ocr(path: Path) -> str:
    """Render each PDF page with PyMuPDF and run Tesseract OCR."""
    try:
        document = fitz.open(path)
    except (fitz.FileDataError, RuntimeError, ValueError) as exc:
        raise OCRError(f"Cannot read PDF file: {path}") from exc

    page_texts: list[str] = []
    try:
        zoom = OCR_RENDER_DPI / 72
        matrix = fitz.Matrix(zoom, zoom)

        for page in document:
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image = Image.open(BytesIO(pixmap.tobytes("png")))
            page_texts.append(pytesseract.image_to_string(image))
    except (TesseractNotFoundError, TesseractError) as exc:
        raise _map_tesseract_error(exc, path) from exc
    finally:
        document.close()

    return "\n\n".join(page_texts)


def _is_meaningful_text(text: str) -> bool:
    """Return True when text contains enough readable content."""
    cleaned = _clean_text(text)
    if not cleaned:
        return False

    alnum_count = sum(1 for character in cleaned if character.isalnum())
    return alnum_count >= MIN_MEANINGFUL_ALNUM_CHARS


def _map_tesseract_error(exc: Exception, path: Path) -> OCRError:
    if isinstance(exc, TesseractNotFoundError):
        return OCRError(
            "Tesseract OCR is not installed or not available on PATH. "
            "Install Tesseract to use OCR."
        )
    return OCRError(f"OCR failed for file: {path}")


def _clean_text(text: str) -> str:
    """Normalize extracted text into a readable plain-text string."""
    lines = [line.strip() for line in text.splitlines()]

    cleaned_lines: list[str] = []
    previous_line_blank = False
    for line in lines:
        is_blank = not line
        if is_blank and previous_line_blank:
            continue
        cleaned_lines.append(line)
        previous_line_blank = is_blank

    return "\n".join(cleaned_lines).strip()
