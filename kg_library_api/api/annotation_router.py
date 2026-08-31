"""
FastAPI router for Knowledge-Graph Annotation API.
Resources are resolved from app.state (set by lifespan in app.py) — no module-level globals.
Supports both manual (human-authored) and agentic (AI-generated) annotations through the same API.
"""

from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from kg_library_api.annotations.manager import AnnotationManager

router = APIRouter(prefix="/annotations", tags=["Annotations"])


# ── Dependency ─────────────────────────────────────────────────────────────────

def get_annotation_manager(request: Request) -> AnnotationManager:
    return request.app.state.ann_mgr


# ── Schemas ────────────────────────────────────────────────────────────────────

class CreateCollectionRequest(BaseModel):
    name: str
    description: str = ""
    collection_id: Optional[str] = None


class CreateAnnotationRequest(BaseModel):
    type: str = Field(description="Annotation type (e.g. 'Evidence', 'Claim', 'Hypothesis', 'Fact')")
    content: str
    annotation_id: Optional[str] = None
    author: str = Field(
        default="human",
        description="Author identifier. Use 'human' for manual edits, or an agent ID for agentic edits."
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: str = ""
    provenance: str = ""
    status: str = "active"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BulkIngestRequest(BaseModel):
    annotations: List[Dict[str, Any]] = Field(
        description="List of annotation dicts. Each may include an 'author' field to distinguish "
                    "human vs. agentic origin."
    )
    relationships: Optional[List[Dict[str, Any]]] = None


class CreateRelationshipRequest(BaseModel):
    target_id: str
    relation_type: str
    target_kind: str = Field(default="KG_NODE", description="'KG_NODE' or 'ANNOTATION'")
    relationship_id: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)


class SubgraphRequest(BaseModel):
    annotation_ids: List[str]


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/collections", status_code=201, summary="Create an annotation collection")
def create_collection(
    req: CreateCollectionRequest,
    mgr: AnnotationManager = Depends(get_annotation_manager),
):
    coll = mgr.create_annotation_collection(
        name=req.name,
        collection_id=req.collection_id,
        description=req.description,
    )
    return coll.to_dict()


@router.post("/collections/{collection_id}/bulk", status_code=200, summary="Bulk ingest annotations")
def bulk_ingest_annotations(
    collection_id: str,
    req: BulkIngestRequest,
    mgr: AnnotationManager = Depends(get_annotation_manager),
):
    """
    Bulk ingest annotations into a collection.
    Both human-authored and agent-generated annotations are accepted.
    Set `author` to `'human'` for manual edits, or an agent identifier for agentic edits.
    """
    result = mgr.bulk_ingest_annotations(
        collection_id=collection_id,
        annotations_data=req.annotations,
        relationships_data=req.relationships,
    )
    return result


@router.post("", status_code=201, summary="Create a single annotation")
def create_annotation(
    req: CreateAnnotationRequest,
    mgr: AnnotationManager = Depends(get_annotation_manager),
):
    """
    Create a single annotation.
    Use `author='human'` for manual edits or an agent/model identifier for agentic edits.
    """
    ann = mgr.create_annotation(
        type=req.type,
        content=req.content,
        annotation_id=req.annotation_id,
        author=req.author,
        confidence=req.confidence,
        source=req.source,
        provenance=req.provenance,
        status=req.status,
        metadata=req.metadata,
    )
    return ann.to_dict()


@router.get("/about/{entity_id}", status_code=200, summary="Get all annotations about a KG entity")
def get_annotations_about_entity(
    entity_id: str,
    mgr: AnnotationManager = Depends(get_annotation_manager),
):
    results = mgr.get_annotations_about_entity(entity_id)
    return {"entity_id": entity_id, "annotations": results}


@router.get("/{annotation_id}", status_code=200, summary="Get an annotation by ID")
def get_annotation(
    annotation_id: str,
    mgr: AnnotationManager = Depends(get_annotation_manager),
):
    ann = mgr.get_annotation(annotation_id)
    if not ann:
        raise HTTPException(status_code=404, detail=f"Annotation '{annotation_id}' not found.")
    return ann.to_dict()


@router.post("/{annotation_id}/relationships", status_code=201, summary="Link an annotation to a node or another annotation")
def create_annotation_relationship(
    annotation_id: str,
    req: CreateRelationshipRequest,
    mgr: AnnotationManager = Depends(get_annotation_manager),
):
    ann = mgr.get_annotation(annotation_id)
    if not ann:
        raise HTTPException(status_code=404, detail=f"Source annotation '{annotation_id}' not found.")

    rel = mgr.add_annotation_relationship(
        source_annotation_id=annotation_id,
        target_id=req.target_id,
        relation_type=req.relation_type,
        target_kind=req.target_kind,
        relationship_id=req.relationship_id,
        properties=req.properties,
    )
    return rel.to_dict()


@router.post("/subgraph", status_code=200, summary="Extract annotation subgraph")
def get_annotation_subgraph(
    req: SubgraphRequest,
    mgr: AnnotationManager = Depends(get_annotation_manager),
):
    subgraph = mgr.get_annotation_subgraph(req.annotation_ids)
    return subgraph
