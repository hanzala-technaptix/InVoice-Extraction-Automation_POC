from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.modules.invoice.schemas import ExtractedInvoiceResponse
from app.modules.pending.models import PendingInvoiceStatus


class PendingInvoiceCreate(BaseModel):
    """Data required to queue an extracted invoice for review."""

    source: str = Field(default="gmail", description="Invoice ingress source")
    gmail_message_id: str = Field(..., description="Gmail IMAP message UID")
    gmail_attachment_id: str = Field(..., description="MIME part index for the PDF")
    pdf_path: str = Field(..., description="Saved PDF path on disk")
    extracted_data: ExtractedInvoiceResponse = Field(
        ...,
        description="Full extraction result used to populate the review form",
    )
    sender_email: Optional[str] = Field(default=None, description="Sender email address")
    subject: Optional[str] = Field(default=None, description="Email subject")
    filename: str = Field(..., description="PDF attachment filename")
    received_at: Optional[datetime] = Field(
        default=None,
        description="When the email was received",
    )


class PendingInvoiceFailureCreate(BaseModel):
    """Data recorded when automatic extraction fails."""

    source: str = Field(default="gmail")
    gmail_message_id: str
    gmail_attachment_id: str
    pdf_path: str = Field(default="")
    sender_email: Optional[str] = None
    subject: Optional[str] = None
    filename: str
    received_at: Optional[datetime] = None
    error_message: str = Field(..., description="Why extraction failed")


class GmailSourceInfo(BaseModel):
    """Gmail metadata shown on the review screen."""

    message_id: str
    attachment_id: str
    sender: Optional[str] = None
    subject: Optional[str] = None
    filename: str
    received_at: Optional[datetime] = None


class PendingInvoiceSummary(BaseModel):
    """Inbox card summary for a pending invoice."""

    id: int
    status: PendingInvoiceStatus
    source: str
    vendor_name: Optional[str] = None
    invoice_number: Optional[str] = None
    sender_email: Optional[str] = None
    subject: Optional[str] = None
    filename: str
    received_at: Optional[datetime] = None
    created_at: datetime
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class PendingInvoiceDetail(PendingInvoiceSummary):
    """
    Full pending invoice payload for the Review/Edit screen.

    extracted_data contains all editable invoice fields:
    vendor, invoice number, date, PO, currency, subtotal, tax, total,
    payment terms, and line items.
    """

    pdf_path: str
    extracted_data: ExtractedInvoiceResponse
    gmail_source: GmailSourceInfo
    approved_invoice_id: Optional[int] = None

    class Config:
        from_attributes = True
