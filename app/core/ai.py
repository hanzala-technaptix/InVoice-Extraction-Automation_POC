from datetime import datetime
from typing import Optional

from openai import APIError, OpenAI
from pydantic import BaseModel, Field

from app.config import get_settings
from app.modules.invoice.schemas import ExtractedInvoiceResponse, ExtractedLineItem

SYSTEM_PROMPT = (
    "Extract invoice header fields and line items from OCR text. "
    "Use null for any field not clearly present. Do not guess or infer missing values. "
    "Return invoice_date as an ISO 8601 date string (YYYY-MM-DD). "
    "Include every line item explicitly listed in the text."
)


class AIConfigurationError(Exception):
    """Raised when OpenAI is not configured correctly."""


class AIExtractionError(Exception):
    """Raised when AI invoice extraction fails."""


class _ExtractedLineItemOutput(BaseModel):
    """Structured output schema for a single invoice line item."""

    description: Optional[str] = Field(default=None, description="Line item description")
    quantity: Optional[float] = Field(default=None, description="Quantity of items")
    unit_price: Optional[float] = Field(default=None, description="Price per unit")
    tax: Optional[float] = Field(default=None, description="Tax amount for line item")
    total: Optional[float] = Field(
        default=None,
        description="Total amount for line item",
    )


class _InvoiceExtractionOutput(BaseModel):
    """Structured output schema returned by the OpenAI Responses API."""

    vendor_name: Optional[str] = Field(default=None, description="Vendor or supplier name")
    invoice_number: Optional[str] = Field(default=None, description="Invoice number")
    invoice_date: Optional[str] = Field(
        default=None,
        description="Invoice date in ISO 8601 format (YYYY-MM-DD)",
    )
    po_number: Optional[str] = Field(default=None, description="Purchase order number")
    currency: Optional[str] = Field(default=None, description="Currency code")
    subtotal: Optional[float] = Field(default=None, description="Subtotal before tax")
    tax: Optional[float] = Field(default=None, description="Total tax amount")
    total: Optional[float] = Field(default=None, description="Total amount including tax")
    payment_terms: Optional[str] = Field(default=None, description="Payment terms")
    line_items: list[_ExtractedLineItemOutput] = Field(
        default_factory=list,
        description="Invoice line items",
    )
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Overall extraction confidence from 0 to 1",
    )


def extract_invoice_from_text(invoice_text: str) -> ExtractedInvoiceResponse:
    """
    Extract structured invoice data from OCR text using OpenAI.

    Args:
        invoice_text: Plain text extracted from an invoice PDF.

    Returns:
        Validated invoice data matching ExtractedInvoiceResponse.

    Raises:
        AIConfigurationError: If the OpenAI API key is missing.
        AIExtractionError: If extraction fails or returns no structured data.
    """
    cleaned_text = invoice_text.strip()
    if not cleaned_text:
        raise AIExtractionError("Invoice text is empty; nothing to extract.")

    client, model = _get_openai_client()

    try:
        response = client.responses.parse(
            model=model,
            instructions=SYSTEM_PROMPT,
            input=cleaned_text,
            text_format=_InvoiceExtractionOutput,
            reasoning={"effort": "minimal"},
            text={"verbosity": "low"},
        )
    except APIError as exc:
        raise AIExtractionError(f"OpenAI API request failed: {exc}") from exc

    parsed = response.output_parsed
    if parsed is None:
        refusal = _find_refusal(response)
        if refusal:
            raise AIExtractionError(f"OpenAI refused to extract invoice data: {refusal}")
        raise AIExtractionError("OpenAI returned no structured invoice data.")

    return _to_extracted_invoice_response(parsed)


def _get_openai_client() -> tuple[OpenAI, str]:
    settings = get_settings()
    api_key = settings.openai_api_key.strip()
    model = settings.openai_model.strip()

    if not api_key:
        raise AIConfigurationError(
            "OpenAI API key is not configured. Set OPENAI_API_KEY in the environment."
        )
    if not model:
        raise AIConfigurationError(
            "OpenAI model is not configured. Set OPENAI_MODEL in the environment."
        )

    return OpenAI(api_key=api_key), model


def _find_refusal(response) -> Optional[str]:
    for output in response.output:
        if output.type != "message":
            continue
        for content in output.content:
            if content.type == "refusal":
                return content.refusal
    return None


def _to_extracted_invoice_response(
    parsed: _InvoiceExtractionOutput,
) -> ExtractedInvoiceResponse:
    line_items = [_to_line_item(line_item) for line_item in parsed.line_items]

    return ExtractedInvoiceResponse(
        vendor_name=parsed.vendor_name,
        invoice_number=parsed.invoice_number,
        invoice_date=_parse_invoice_date(parsed.invoice_date),
        po_number=parsed.po_number,
        currency=parsed.currency,
        subtotal=parsed.subtotal,
        tax=parsed.tax,
        total=parsed.total,
        payment_terms=parsed.payment_terms,
        line_items=line_items,
        confidence_score=parsed.confidence_score,
    )


def _to_line_item(item: _ExtractedLineItemOutput) -> ExtractedLineItem:
    return ExtractedLineItem(
        description=item.description,
        quantity=item.quantity,
        unit_price=item.unit_price,
        tax=item.tax,
        total=item.total,
    )


def _parse_invoice_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None

    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise AIExtractionError(f"Invalid invoice_date returned by AI: {value}") from exc

    return parsed.replace(tzinfo=None)
