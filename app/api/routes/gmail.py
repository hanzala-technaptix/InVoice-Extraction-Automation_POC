from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.modules.gmail.poller import GmailPollResult, poll_gmail_inbox
from app.modules.gmail.service import (
    GmailServiceError,
    extract_invoice_from_gmail_attachment,
    gmail_connection_status,
    list_gmail_invoice_messages,
    list_gmail_pdf_attachments,
)
from app.modules.invoice.schemas import ExtractedInvoiceResponse

router = APIRouter(prefix="/gmail", tags=["gmail"])


class GmailStatusResponse(BaseModel):
    configured: bool
    connected: bool


class GmailPdfAttachmentResponse(BaseModel):
    message_id: str
    attachment_id: str
    filename: str


class GmailMessageResponse(BaseModel):
    message_id: str
    subject: str
    sender: str
    received_at: datetime | None
    pdf_attachments: list[GmailPdfAttachmentResponse]


class GmailExtractRequest(BaseModel):
    message_id: str = Field(..., description="Gmail IMAP message UID")
    attachment_id: str = Field(..., description="MIME part index for the PDF attachment")


class GmailSourceMetadata(BaseModel):
    message_id: str
    attachment_id: str
    filename: str
    pdf_path: str


class GmailExtractResponse(BaseModel):
    invoice: ExtractedInvoiceResponse
    source: GmailSourceMetadata


class GmailPollResponse(BaseModel):
    configured: bool
    processed: int
    queued: int
    skipped: int
    failed: int
    errors: list[str] = Field(default_factory=list)


@router.get("/status", response_model=GmailStatusResponse)
def get_gmail_status() -> GmailStatusResponse:
    """Return whether Gmail IMAP credentials are configured and working."""
    status_data = gmail_connection_status()
    return GmailStatusResponse(
        configured=bool(status_data["configured"]),
        connected=bool(status_data["connected"]),
    )


@router.get("/messages", response_model=list[GmailMessageResponse])
def get_gmail_messages(
    max_results: int = Query(default=20, ge=1, le=50),
) -> list[GmailMessageResponse]:
    """List Gmail messages that contain PDF attachments."""
    try:
        messages = list_gmail_invoice_messages(max_results=max_results)
    except GmailServiceError as exc:
        raise _gmail_api_error(exc) from exc

    return [_to_message_response(message) for message in messages]


@router.get(
    "/messages/{message_id}/attachments",
    response_model=list[GmailPdfAttachmentResponse],
)
def get_gmail_message_attachments(message_id: str) -> list[GmailPdfAttachmentResponse]:
    """List PDF attachments for one Gmail message."""
    try:
        attachments = list_gmail_pdf_attachments(message_id)
    except GmailServiceError as exc:
        raise _gmail_api_error(exc) from exc

    return [
        GmailPdfAttachmentResponse(
            message_id=attachment.message_id,
            attachment_id=attachment.attachment_id,
            filename=attachment.filename,
        )
        for attachment in attachments
    ]


@router.post("/extract", response_model=GmailExtractResponse)
def extract_invoice_from_gmail(request: GmailExtractRequest) -> GmailExtractResponse:
    """
    Download a Gmail PDF attachment and run the existing invoice extraction pipeline.

    Returns extracted invoice data for user review. Does not auto-approve.
    """
    try:
        result = extract_invoice_from_gmail_attachment(
            message_id=request.message_id,
            attachment_id=request.attachment_id,
        )
    except GmailServiceError as exc:
        raise _gmail_extract_error(exc) from exc

    return GmailExtractResponse(
        invoice=result.invoice,
        source=GmailSourceMetadata(
            message_id=result.message_id,
            attachment_id=result.attachment_id,
            filename=result.filename,
            pdf_path=str(result.pdf_path),
        ),
    )


@router.post("/poll", response_model=GmailPollResponse)
def poll_gmail_now(
    max_results: int = Query(default=20, ge=1, le=50),
) -> GmailPollResponse:
    """
    Manually poll Gmail for new PDF attachments and queue them for review.

    The same poll also runs automatically in the background on server startup.
    """
    result = poll_gmail_inbox(max_results=max_results)
    return _to_poll_response(result)


def _to_message_response(message) -> GmailMessageResponse:
    return GmailMessageResponse(
        message_id=message.message_id,
        subject=message.subject,
        sender=message.sender,
        received_at=message.received_at,
        pdf_attachments=[
            GmailPdfAttachmentResponse(
                message_id=attachment.message_id,
                attachment_id=attachment.attachment_id,
                filename=attachment.filename,
            )
            for attachment in message.pdf_attachments
        ],
    )


def _to_poll_response(result: GmailPollResult) -> GmailPollResponse:
    return GmailPollResponse(
        configured=result.configured,
        processed=result.processed,
        queued=result.queued,
        skipped=result.skipped,
        failed=result.failed,
        errors=result.errors,
    )


def _gmail_api_error(exc: GmailServiceError) -> HTTPException:
    message = str(exc)
    if _is_not_configured(message):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=message,
        )
    if _is_not_connected(message):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
        )
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=message,
    )


def _gmail_extract_error(exc: GmailServiceError) -> HTTPException:
    message = str(exc)
    if _is_not_configured(message):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=message,
        )
    if _is_not_connected(message):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
        )
    if _is_client_error(message):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=message,
    )


def _is_not_configured(message: str) -> bool:
    return "not configured" in message.lower()


def _is_not_connected(message: str) -> bool:
    lowered = message.lower()
    return "login failed" in lowered or "not connected" in lowered


def _is_client_error(message: str) -> bool:
    lowered = message.lower()
    return (
        "not found on message" in lowered
        or "only pdf files are supported" in lowered
        or "empty" in lowered
        or "not a valid pdf" in lowered
    )
