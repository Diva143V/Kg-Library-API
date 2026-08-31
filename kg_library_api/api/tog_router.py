"""
FastAPI router for Think-on-Graph (ToG) Worker API deliverable.
Resources are resolved from app.state (set by lifespan in app.py) — no module-level globals.
"""

from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from kg_library_api.tog.worker import ToGWorker

router = APIRouter(prefix="/tog", tags=["Think-on-Graph Worker"])


# ── Dependency ─────────────────────────────────────────────────────────────────

def get_tog_worker(request: Request) -> ToGWorker:
    return request.app.state.tog_worker


# ── Schemas ────────────────────────────────────────────────────────────────────

class ToGQueryRequest(BaseModel):
    query: str = Field(description="Natural-language or structured query over the knowledge graph")
    include_annotations: bool = True
    max_depth: int = Field(default=3, ge=1, le=10, description="Graph traversal depth (1–10)")
    start_entities: Optional[List[str]] = Field(
        default=None,
        description="Optional list of node IDs to start traversal from. Auto-detected from query if omitted."
    )
    traversal_mode: str = Field(
        default="hybrid",
        description="Traversal mode: 'manual' (deterministic), 'ai' (LLM-guided), or 'hybrid' (deterministic + AI escalation)"
    )
    enable_domain_packs: bool = Field(
        default=True,
        description="Whether to query registered domain pack tools for external evidence"
    )
    ai_enabled: Optional[bool] = Field(default=None, description="Override AI toggle for this request")
    max_ai_calls: Optional[int] = Field(default=None, ge=0, description="Override max AI calls for this request")


class ToGQueryResponse(BaseModel):
    answer: str
    knowledge_paths: List[Dict[str, Any]]
    annotations: List[Dict[str, Any]]
    annotation_paths: List[Dict[str, Any]]
    perspectives: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    provenance: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class PackQueryRequest(BaseModel):
    pack_name: str
    tool_name: str
    payload: Dict[str, Any]


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/query", response_model=ToGQueryResponse, status_code=200)
def query_tog(
    req: ToGQueryRequest,
    worker: ToGWorker = Depends(get_tog_worker),
):
    """
    Primary Think-on-Graph query endpoint.
    Executes query understanding, graph traversal (deterministic or AI-guided),
    evidence context retrieval, and structured multi-perspective answer synthesis.

    Works on **any domain** — the engine is fully data-driven by the graph content.
    Manual edits (human) and agentic edits (AI) both flow through this same pipeline.
    """
    result = worker.execute_query(
        query=req.query,
        include_annotations=req.include_annotations,
        max_depth=req.max_depth,
        start_entities=req.start_entities,
        traversal_mode=req.traversal_mode,
        enable_domain_packs=req.enable_domain_packs,
        ai_enabled=req.ai_enabled,
        max_ai_calls=req.max_ai_calls,
    )
    return result


@router.get("/status", status_code=200, summary="ToG engine configuration and health")
def tog_status(worker: ToGWorker = Depends(get_tog_worker)):
    """Returns the current AI gateway policy and traversal configuration."""
    policy = worker.ai_gateway.policy
    return {
        "status": "ok",
        "traversal_mode": policy.traversal_mode,
        "ai_enabled": policy.ai_enabled,
        "max_ai_calls": policy.max_ai_calls,
        "ai_budget_usd": policy.ai_budget,
        "local_first": policy.local_first,
        "cloud_fallback": policy.cloud_fallback,
    }


@router.get("/packs", status_code=200, summary="List registered domain packs")
def list_packs(worker: ToGWorker = Depends(get_tog_worker)):
    """List all registered domain packs and their tool manifests."""
    return worker.retriever.tool_manager.list_packs()


@router.post("/packs/query", status_code=200, summary="Execute a domain pack tool directly")
def query_pack(
    req: PackQueryRequest,
    worker: ToGWorker = Depends(get_tog_worker),
):
    """Execute a query/action directly on a specific domain pack tool."""
    try:
        res = worker.retriever.tool_manager.execute_tool(
            pack_name=req.pack_name,
            tool_name=req.tool_name,
            payload=req.payload,
        )
        return res.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
