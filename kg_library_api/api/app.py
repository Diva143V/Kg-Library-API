"""
KG Library API — Main FastAPI Application.
Uses FastAPI lifespan for clean startup/shutdown of shared resources.
All routers are mounted under /v1/ for forward-compatible versioning.
"""

import logging
import uuid
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from kg_library_api.config import settings

logger = logging.getLogger("kg_library_api.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialise all shared resources once at startup and attach them to app.state.
    Routers retrieve them via Depends() — no module-level globals.
    """
    settings.configure_logging()
    logger.info("KG Library API starting up...")

    from kg_library_api.core.storage import SQLStorageEngine, InMemoryStorageEngine
    from kg_library_api.core.kg import KnowledgeGraph
    from kg_library_api.annotations.db_manager import SQLAnnotationStorage
    from kg_library_api.annotations.manager import AnnotationManager
    from kg_library_api.tog.worker import ToGWorker
    from kg_library_api.ai.policy import AIEscalationPolicy
    from kg_library_api.ai.gateway import AIGateway

    if settings.database_url:
        logger.info("Connecting to SQL database: %s", settings.database_url[:30] + "…")
        storage = SQLStorageEngine(settings.database_url)
        ann_storage = SQLAnnotationStorage(settings.database_url)
        kg = KnowledgeGraph(storage)
        ann_mgr = AnnotationManager(base_kg=kg, db_storage=ann_storage)
    else:
        logger.info("No KG_LIBRARY_DATABASE_URL set — using in-memory storage.")
        kg = KnowledgeGraph(InMemoryStorageEngine())
        ann_mgr = AnnotationManager(base_kg=kg)

    default_policy = AIEscalationPolicy(
        ai_enabled=settings.ai_enabled,
        max_ai_calls=settings.max_ai_calls,
        ai_budget=settings.ai_budget,
        local_first=settings.local_first,
        cloud_fallback=settings.cloud_fallback,
    )
    ai_gateway = AIGateway(policy=default_policy)
    tog_worker = ToGWorker(kg, ann_mgr, ai_gateway=ai_gateway)

    app.state.kg = kg
    app.state.ann_mgr = ann_mgr
    app.state.tog_worker = tog_worker

    logger.info("KG Library API ready.")
    yield

    logger.info("KG Library API shutting down.")


# ── Application ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="KG Library API",
    description=(
        "A domain-agnostic, reusable Knowledge Graph and Think-on-Graph (ToG) reasoning API. "
        "Supports any domain: plug in your data, annotate with expert knowledge, and query with "
        "deterministic graph traversal or AI-augmented reasoning."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ─────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next: Callable) -> Response:
    """Attach a correlation ID to every request for end-to-end traceability."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    logger.info(
        "→ %s %s | correlation_id=%s",
        request.method,
        request.url.path,
        correlation_id,
    )
    response: Response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    logger.info(
        "← %s %s | status=%s | correlation_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        correlation_id,
    )
    return response


# ── Routers ────────────────────────────────────────────────────────────────────

from kg_library_api.api.graph_router import router as graph_router
from kg_library_api.api.annotation_router import router as annotation_router
from kg_library_api.api.tog_router import router as tog_router

app.include_router(graph_router, prefix="/v1")
app.include_router(annotation_router, prefix="/v1")
app.include_router(tog_router, prefix="/v1")


# ── Root ───────────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "kg-library-api", "version": "1.0.0"}
