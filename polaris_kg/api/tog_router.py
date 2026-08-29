"""
FastAPI router for Think-on-Graph (ToG) Worker API deliverable.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import os
from polaris_kg.core.kg import KnowledgeGraph
from polaris_kg.core.storage import SQLStorageEngine
from polaris_kg.annotations.db_manager import SQLAnnotationStorage
from polaris_kg.annotations.manager import AnnotationManager
from polaris_kg.tog.worker import ToGWorker

router = APIRouter(prefix="/tog", tags=["Think-on-Graph Worker"])

_db_url = os.getenv("POLARIS_DATABASE_URL")
if _db_url:
    _sql_storage = SQLStorageEngine(_db_url)
    _shared_kg = KnowledgeGraph(_sql_storage)
    _db_ann_storage = SQLAnnotationStorage(_db_url)
    _shared_ann_mgr = AnnotationManager(base_kg=_shared_kg, db_storage=_db_ann_storage)
else:
    _shared_kg = KnowledgeGraph()
    _shared_ann_mgr = AnnotationManager(_shared_kg)

_shared_tog_worker = ToGWorker(_shared_kg, _shared_ann_mgr)


def get_tog_worker() -> ToGWorker:
    return _shared_tog_worker


class ToGQueryRequest(BaseModel):
    query: str
    include_annotations: bool = True
    max_depth: int = 3
    start_entities: Optional[List[str]] = None
    traversal_mode: str = Field(default="manual", description="Traversal mode: 'manual', 'ai', or 'hybrid'")
    enable_domain_packs: bool = True
    ai_enabled: Optional[bool] = None
    max_ai_calls: Optional[int] = None


class ToGQueryResponse(BaseModel):
    answer: str
    knowledge_paths: List[Dict[str, Any]]
    annotations: List[Dict[str, Any]]
    annotation_paths: List[Dict[str, Any]]
    perspectives: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    provenance: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@router.post("/query", response_model=ToGQueryResponse, status_code=200)
def query_tog(
    req: ToGQueryRequest,
    worker: ToGWorker = Depends(get_tog_worker),
):
    """
    Primary Think-on-Graph query endpoint.
    Executes query understanding, graph traversal (manual deterministic or AI-guided), evidence context retrieval, and structured answer synthesis.
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


class PackQueryRequest(BaseModel):
    pack_name: str
    tool_name: str
    payload: Dict[str, Any]


@router.get("/packs", status_code=200)
def list_packs(worker: ToGWorker = Depends(get_tog_worker)):
    """
    List all registered domain packs and their manifests.
    """
    return worker.retriever.tool_manager.list_packs()


@router.post("/packs/query", status_code=200)
def query_pack(
    req: PackQueryRequest,
    worker: ToGWorker = Depends(get_tog_worker),
):
    """
    Execute a query/action directly on a specific domain pack tool.
    """
    try:
        res = worker.retriever.tool_manager.execute_tool(
            pack_name=req.pack_name,
            tool_name=req.tool_name,
            payload=req.payload,
        )
        return res.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
