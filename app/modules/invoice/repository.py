from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload, sessionmaker

from app.config import get_settings
from app.modules.invoice.models import Base, Invoice, InvoiceItem
from app.modules.invoice.schemas import (
    ApprovedInvoiceRequest,
    ApprovedInvoiceResponse,
    InvoiceLineItemResponse,
)

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


class RepositoryError(Exception):
    """Raised when a database operation fails."""


def init_db() -> None:
    """Create database tables if they do not exist."""
    import app.modules.pending.models  # noqa: F401 — register PendingInvoice with Base

    engine = _get_engine()
    Base.metadata.create_all(bind=engine)


def save_invoice(invoice_data: ApprovedInvoiceRequest) -> ApprovedInvoiceResponse:
    """
    Save an approved invoice and its line items in one transaction.

    Args:
        invoice_data: Validated invoice data ready for persistence.

    Returns:
        Saved invoice with database IDs.

    Raises:
        RepositoryError: If the save operation fails.
    """
    session = _get_session()
    try:
        invoice = _build_invoice(invoice_data)
        session.add(invoice)
        session.commit()
        session.refresh(invoice)
        return _to_approved_invoice_response(invoice)
    except SQLAlchemyError as exc:
        session.rollback()
        raise RepositoryError("Failed to save invoice.") from exc
    finally:
        session.close()


def get_all_invoices() -> list[ApprovedInvoiceResponse]:
    """
    Retrieve all saved invoices with their line items.

    Raises:
        RepositoryError: If the query fails.
    """
    session = _get_session()
    try:
        invoices = session.scalars(
            select(Invoice)
            .options(joinedload(Invoice.items))
            .order_by(Invoice.created_at.desc())
        ).unique().all()
        return [_to_approved_invoice_response(invoice) for invoice in invoices]
    except SQLAlchemyError as exc:
        session.rollback()
        raise RepositoryError("Failed to retrieve invoices.") from exc
    finally:
        session.close()


def get_invoice_by_id(invoice_id: int) -> ApprovedInvoiceResponse | None:
    """
    Retrieve one invoice and its line items by ID.

    Raises:
        RepositoryError: If the query fails.
    """
    session = _get_session()
    try:
        invoice = session.scalars(
            select(Invoice)
            .options(joinedload(Invoice.items))
            .where(Invoice.id == invoice_id)
        ).unique().first()
        if invoice is None:
            return None
        return _to_approved_invoice_response(invoice)
    except SQLAlchemyError as exc:
        session.rollback()
        raise RepositoryError("Failed to retrieve invoice.") from exc
    finally:
        session.close()


def _get_engine() -> Engine:
    global _engine, _SessionLocal

    if _engine is None:
        settings = get_settings()
        _ensure_sqlite_directory(settings.database_url)
        _engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},
        )
        _SessionLocal = sessionmaker(
            bind=_engine,
            autoflush=False,
            autocommit=False,
        )

    return _engine


def _get_session() -> Session:
    _get_engine()
    assert _SessionLocal is not None
    return _SessionLocal()


def _ensure_sqlite_directory(database_url: str) -> None:
    if not database_url.startswith("sqlite:///"):
        return

    db_file = database_url.removeprefix("sqlite:///")
    Path(db_file).parent.mkdir(parents=True, exist_ok=True)


def _build_invoice(invoice_data: ApprovedInvoiceRequest) -> Invoice:
    invoice = Invoice(
        vendor_name=invoice_data.vendor_name,
        invoice_number=invoice_data.invoice_number,
        invoice_date=invoice_data.invoice_date,
        po_number=invoice_data.po_number,
        currency=invoice_data.currency,
        subtotal=invoice_data.subtotal,
        tax=invoice_data.tax,
        total=invoice_data.total,
        payment_terms=invoice_data.payment_terms,
    )

    for line_item in invoice_data.line_items:
        invoice.items.append(
            InvoiceItem(
                description=line_item.description,
                quantity=line_item.quantity,
                unit_price=line_item.unit_price,
                tax=line_item.tax,
                total=line_item.total,
            )
        )

    return invoice


def _to_approved_invoice_response(invoice: Invoice) -> ApprovedInvoiceResponse:
    return ApprovedInvoiceResponse(
        id=invoice.id,
        vendor_name=invoice.vendor_name,
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date,
        po_number=invoice.po_number,
        currency=invoice.currency,
        subtotal=invoice.subtotal,
        tax=invoice.tax,
        total=invoice.total,
        payment_terms=invoice.payment_terms,
        line_items=[
            InvoiceLineItemResponse(
                id=item.id,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                tax=item.tax,
                total=item.total,
            )
            for item in invoice.items
        ],
        created_at=invoice.created_at,
    )
