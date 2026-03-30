"""FastAPI application factory."""
import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os

from api.routers import chat, widget, tenants, knowledge, leads, conversations

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("PitronAgent API starting up")
    yield
    logger.info("PitronAgent API shutting down")


app = FastAPI(
    title="PitronAgent API",
    version="1.0.0",
    description="Multi-tenant AI agent platform for small businesses",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Broad CORS because the widget is embedded on arbitrary client sites.
# Per-tenant origin validation happens at the application level in the chat endpoint.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ── Request logging middleware ────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = (time.time() - start) * 1000
    logger.info(
        "%s %s %s %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )
    return response


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(chat.router, prefix="/v1", tags=["chat"])
app.include_router(widget.router, prefix="/v1", tags=["widget"])
app.include_router(tenants.router, prefix="/v1", tags=["admin"])
app.include_router(knowledge.router, prefix="/v1", tags=["admin"])
app.include_router(leads.router, prefix="/v1", tags=["admin"])
app.include_router(conversations.router, prefix="/v1", tags=["admin"])

# ── Widget static files ───────────────────────────────────────────────────────
_widget_dir = os.path.join(os.path.dirname(__file__), "..", "widget")
if os.path.isdir(_widget_dir):
    app.mount("/widget", StaticFiles(directory=_widget_dir), name="widget")


# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "version": "1.0.0"}


# ── Global error handler ──────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error."},
    )
