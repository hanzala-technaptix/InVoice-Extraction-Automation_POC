from contextlib import asynccontextmanager
import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.gmail import router as gmail_router
from app.api.routes.invoice import router as invoice_router
from app.api.routes.pending import router as pending_router
from app.config import get_settings
from app.modules.gmail.poller import poll_gmail_inbox
from app.modules.invoice.service import initialize

logger = logging.getLogger(__name__)


async def _gmail_poll_loop() -> None:
    """Poll Gmail on an interval and queue new invoices for review."""
    settings = get_settings()
    if not settings.gmail_poll_enabled:
        return

    interval = settings.gmail_poll_interval_seconds
    logger.info("Gmail polling enabled (every %ss)", interval)

    while True:
        try:
            result = await asyncio.to_thread(poll_gmail_inbox)
            if result.configured and (result.queued or result.failed or result.skipped):
                logger.info(
                    "Gmail poll: processed=%s queued=%s skipped=%s failed=%s",
                    result.processed,
                    result.queued,
                    result.skipped,
                    result.failed,
                )
        except Exception:
            logger.exception("Gmail poll failed")

        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup and shutdown tasks for the application."""
    initialize()

    settings = get_settings()
    poll_task = None
    if settings.gmail_poll_enabled and settings.gmail_email and settings.gmail_app_password:
        result = await asyncio.to_thread(poll_gmail_inbox)
        if result.configured:
            logger.info(
                "Initial Gmail poll: processed=%s queued=%s skipped=%s failed=%s",
                result.processed,
                result.queued,
                result.skipped,
                result.failed,
            )
        poll_task = asyncio.create_task(_gmail_poll_loop())

    yield

    if poll_task is not None:
        poll_task.cancel()
        try:
            await poll_task
        except asyncio.CancelledError:
            pass


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Accept", "Content-Type"],
)

app.include_router(invoice_router)
app.include_router(gmail_router)
app.include_router(pending_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Simple health-check endpoint."""
    return {"status": "ok"}
