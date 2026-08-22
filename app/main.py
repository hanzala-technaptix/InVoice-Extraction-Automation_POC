from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.invoice import router as invoice_router
from app.config import get_settings
from app.modules.invoice.service import initialize


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup and shutdown tasks for the application."""
    initialize()
    yield


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


@app.get("/health")
def health_check() -> dict[str, str]:
    """Simple health-check endpoint."""
    return {"status": "ok"}
