from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class InvoiceLineItemBase(BaseModel):
    """Base schema for invoice line items."""

    description: str = Field(..., description="Line item description")
    quantity: float = Field(..., gt=0, description="Quantity of items")
    unit_price: float = Field(..., ge=0, description="Price per unit")
    tax: float = Field(default=0, ge=0, description="Tax amount for line item")
    total: float = Field(..., ge=0, description="Total amount for line item (quantity * unit_price + tax)")


class InvoiceLineItemCreate(InvoiceLineItemBase):
    """Schema for creating a new line item."""

    pass


class InvoiceLineItemResponse(InvoiceLineItemBase):
    """Schema for line item in responses."""

    id: Optional[int] = Field(default=None, description="Line item ID")

    class Config:
        from_attributes = True


class ExtractedLineItem(BaseModel):
    """Schema for a line item returned from OCR/AI extraction."""

    description: Optional[str] = Field(default=None, description="Line item description")
    quantity: Optional[float] = Field(default=None, description="Quantity of items")
    unit_price: Optional[float] = Field(default=None, description="Price per unit")
    tax: Optional[float] = Field(default=None, description="Tax amount for line item")
    total: Optional[float] = Field(default=None, description="Total amount for line item")


class InvoiceHeaderBase(BaseModel):
    """Base schema for invoice header/details."""

    vendor_name: str = Field(..., description="Vendor/Supplier name")
    invoice_number: str = Field(..., description="Invoice number/ID")
    invoice_date: datetime = Field(..., description="Invoice date")
    po_number: Optional[str] = Field(default=None, description="Purchase Order number")
    currency: str = Field(default="USD", description="Currency code (e.g., USD, EUR)")
    subtotal: float = Field(..., ge=0, description="Subtotal before tax")
    tax: float = Field(..., ge=0, description="Total tax amount")
    total: float = Field(..., ge=0, description="Total amount including tax")
    payment_terms: Optional[str] = Field(default=None, description="Payment terms (e.g., Net 30)")


class InvoiceHeaderCreate(InvoiceHeaderBase):
    """Schema for creating invoice header."""

    pass


class InvoiceHeaderResponse(InvoiceHeaderBase):
    """Schema for invoice header in responses."""

    id: Optional[int] = Field(default=None, description="Invoice ID")

    class Config:
        from_attributes = True


class ExtractedInvoiceResponse(BaseModel):
    """Schema for extracted invoice data returned from OCR/AI processing."""

    vendor_name: Optional[str] = Field(default=None, description="Extracted vendor name")
    invoice_number: Optional[str] = Field(default=None, description="Extracted invoice number")
    invoice_date: Optional[datetime] = Field(default=None, description="Extracted invoice date")
    po_number: Optional[str] = Field(default=None, description="Extracted PO number")
    currency: Optional[str] = Field(default=None, description="Extracted currency")
    subtotal: Optional[float] = Field(default=None, description="Extracted subtotal")
    tax: Optional[float] = Field(default=None, description="Extracted tax")
    total: Optional[float] = Field(default=None, description="Extracted total")
    payment_terms: Optional[str] = Field(default=None, description="Extracted payment terms")
    line_items: list[ExtractedLineItem] = Field(
        default_factory=list,
        description="Extracted line items",
    )
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="OCR/AI confidence score (0-1)",
    )


class ApprovedInvoiceRequest(BaseModel):
    """Schema for user-approved/edited invoice data before submission to database."""

    vendor_name: str = Field(..., description="Vendor/Supplier name")
    invoice_number: str = Field(..., description="Invoice number/ID")
    invoice_date: datetime = Field(..., description="Invoice date")
    po_number: Optional[str] = Field(default=None, description="Purchase Order number")
    currency: str = Field(default="USD", description="Currency code")
    subtotal: float = Field(..., ge=0, description="Subtotal before tax")
    tax: float = Field(..., ge=0, description="Total tax amount")
    total: float = Field(..., ge=0, description="Total amount including tax")
    payment_terms: Optional[str] = Field(default=None, description="Payment terms")
    line_items: list[InvoiceLineItemCreate] = Field(
        ...,
        min_items=1,
        description="Invoice line items (at least one required)",
    )
    pending_invoice_id: Optional[int] = Field(
        default=None,
        description="Pending invoice to mark saved after approval (Gmail flow)",
    )


class ApprovedInvoiceResponse(BaseModel):
    """Schema for approved invoice returned after successful database persistence."""

    id: int = Field(..., description="Invoice ID from database")
    vendor_name: str = Field(..., description="Vendor/Supplier name")
    invoice_number: str = Field(..., description="Invoice number/ID")
    invoice_date: datetime = Field(..., description="Invoice date")
    po_number: Optional[str] = Field(default=None, description="Purchase Order number")
    currency: str = Field(default="USD", description="Currency code")
    subtotal: float = Field(..., ge=0, description="Subtotal before tax")
    tax: float = Field(..., ge=0, description="Total tax amount")
    total: float = Field(..., ge=0, description="Total amount including tax")
    payment_terms: Optional[str] = Field(default=None, description="Payment terms")
    line_items: list[InvoiceLineItemResponse] = Field(
        default_factory=list,
        description="Invoice line items with IDs",
    )
    created_at: datetime = Field(..., description="Timestamp when invoice was saved")

    class Config:
        from_attributes = True
