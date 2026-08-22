from dataclasses import dataclass, field
from typing import Optional, Union

from app.modules.invoice.schemas import (
    ApprovedInvoiceRequest,
    ExtractedInvoiceResponse,
    ExtractedLineItem,
    InvoiceLineItemBase,
)

InvoiceData = Union[ExtractedInvoiceResponse, ApprovedInvoiceRequest]
LineItemData = Union[ExtractedLineItem, InvoiceLineItemBase]

AMOUNT_TOLERANCE = 0.01


@dataclass
class ValidationResult:
    """Validation outcome for invoice data."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


def validate_invoice(invoice: InvoiceData) -> ValidationResult:
    """
    Validate invoice header fields, line items, and amount consistency.

    Does not modify the invoice data.

    Args:
        invoice: Extracted or user-approved invoice data.

    Returns:
        ValidationResult with blocking errors and non-blocking warnings.
    """
    result = ValidationResult()

    _validate_header(invoice, result)
    _validate_line_items(invoice.line_items, result)
    _validate_amount_consistency(invoice, result)

    return result


def _validate_header(invoice: InvoiceData, result: ValidationResult) -> None:
    if _is_missing_str(invoice.vendor_name):
        result.errors.append("Vendor name is required.")

    if _is_missing_str(invoice.invoice_number):
        result.errors.append("Invoice number is required.")

    if _is_missing_str(invoice.currency):
        result.errors.append("Currency is required.")

    if invoice.subtotal is not None and invoice.subtotal < 0:
        result.errors.append("Subtotal cannot be negative.")

    if invoice.tax is not None and invoice.tax < 0:
        result.errors.append("Tax cannot be negative.")

    if invoice.total is not None and invoice.total < 0:
        result.errors.append("Total cannot be negative.")


def _validate_line_items(
    line_items: list[LineItemData],
    result: ValidationResult,
) -> None:
    if not line_items:
        result.errors.append("At least one line item is required.")
        return

    for index, item in enumerate(line_items, start=1):
        prefix = f"Line item {index}"

        if _is_missing_str(item.description):
            result.errors.append(f"{prefix}: description is required.")

        if item.quantity is None:
            result.errors.append(f"{prefix}: quantity is required.")
        elif item.quantity <= 0:
            result.errors.append(f"{prefix}: quantity must be greater than zero.")

        if item.unit_price is None:
            result.errors.append(f"{prefix}: unit price is required.")
        elif item.unit_price < 0:
            result.errors.append(f"{prefix}: unit price cannot be negative.")

        if item.tax is not None and item.tax < 0:
            result.errors.append(f"{prefix}: tax cannot be negative.")

        if item.total is None:
            result.errors.append(f"{prefix}: total is required.")
        elif item.total < 0:
            result.errors.append(f"{prefix}: total cannot be negative.")

        if (
            item.quantity is not None
            and item.unit_price is not None
            and item.total is not None
        ):
            item_tax = item.tax if item.tax is not None else 0.0
            expected_total = (item.quantity * item.unit_price) + item_tax
            if not _amounts_match(item.total, expected_total):
                result.warnings.append(
                    f"{prefix}: total {item.total:.2f} does not match "
                    f"quantity x unit price + tax ({expected_total:.2f})."
                )


def _validate_amount_consistency(
    invoice: InvoiceData,
    result: ValidationResult,
) -> None:
    if (
        invoice.subtotal is not None
        and invoice.tax is not None
        and invoice.total is not None
    ):
        expected_invoice_total = invoice.subtotal + invoice.tax
        if not _amounts_match(invoice.total, expected_invoice_total):
            result.warnings.append(
                f"Invoice total {invoice.total:.2f} does not match "
                f"subtotal + tax ({expected_invoice_total:.2f})."
            )

    if not invoice.line_items:
        return

    if invoice.subtotal is None:
        return

    line_item_totals = [
        item.total for item in invoice.line_items if item.total is not None
    ]
    if len(line_item_totals) != len(invoice.line_items):
        return

    line_items_subtotal = sum(line_item_totals)
    if not _amounts_match(invoice.subtotal, line_items_subtotal):
        result.warnings.append(
            f"Subtotal {invoice.subtotal:.2f} does not match the sum of "
            f"line item totals ({line_items_subtotal:.2f})."
        )


def _is_missing_str(value: Optional[str]) -> bool:
    return value is None or not value.strip()


def _amounts_match(actual: float, expected: float) -> bool:
    return abs(actual - expected) <= AMOUNT_TOLERANCE
