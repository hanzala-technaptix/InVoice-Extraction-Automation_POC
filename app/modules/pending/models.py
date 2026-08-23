from datetime import datetime
from enum import StrEnum
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.invoice.models import Base


class PendingInvoiceStatus(StrEnum):
    """Lifecycle status for invoices awaiting human review."""

    PENDING_REVIEW = "pending_review"
    FAILED = "failed"
    SAVED = "saved"


class PendingInvoice(Base):
    """Extracted invoice queued for user review before approval."""

    __tablename__ = "pending_invoices"
    __table_args__ = (
        UniqueConstraint(
            "gmail_message_id",
            "gmail_attachment_id",
            name="uq_pending_gmail_attachment",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default=PendingInvoiceStatus.PENDING_REVIEW,
    )
    source: Mapped[str] = mapped_column(String, nullable=False, default="gmail")

    gmail_message_id: Mapped[str] = mapped_column(String, nullable=False)
    gmail_attachment_id: Mapped[str] = mapped_column(String, nullable=False)

    pdf_path: Mapped[str] = mapped_column(String, nullable=False)
    extracted_json: Mapped[str] = mapped_column(Text, nullable=False)

    vendor_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    invoice_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sender_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_invoice_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
