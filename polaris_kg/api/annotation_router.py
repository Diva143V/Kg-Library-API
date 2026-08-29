"""
FastAPI router for Knowledge-Graph Annotation API deliverable.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from polaris_kg.annotations.manager import AnnotationManager

router = APIRouter(prefix="/annotations", tags=["Annotations"])

# Global singleton or dependency instance
_annotation_manager = AnnotationManager()


def get_annotation_manager() -> AnnotationManager:
    return _annotation_manager


class CreateCollectionRequest(BaseModel):
    name: str
    description: str = ""
    collection_id: Optional[str] = None


class CreateAnnotationRequest(BaseModel):
    type: str
    content: str
    annotation_id: Optional[str] = None
    author: str = "expert"
    confidence: float = 1.0
    source: str = ""
    provenance: str = ""
    status: str = "active"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BulkIngestRequest(BaseModel):
    annotations: List[Dict[str, Any]]
    relationships: Optional[List[Dict[str, Any]]] = None


class CreateRelationshipRequest(BaseModel):
    target_id: str
    relation_type: str
    target_kind: str = "KG_NODE"
    relationship_id: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)


class SubgraphRequest(BaseModel):
    annotation_ids: List[str]


@router.post("/collections", status_code=201)
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


@router.post("/collections/{collection_id}/bulk", status_code=200)
def bulk_ingest_annotations(
    collection_id: str,
    req: BulkIngestRequest,
    mgr: AnnotationManager = Depends(get_annotation_manager),
):
    result = mgr.bulk_ingest_annotations(
        collection_id=collection_id,
        annotations_data=req.annotations,
        relationships_data=req.relationships,
    )
    return result


@router.post("", status_code=201)
def create_annotation(
    req: CreateAnnotationRequest,
    mgr: AnnotationManager = Depends(get_annotation_manager),
):
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


@router.get("/{annotation_id}", status_code=200)
def get_annotation(
    annotation_id: str,
    mgr: AnnotationManager = Depends(get_annotation_manager),
):
    ann = mgr.get_annotation(annotation_id)
    if not ann:
        raise HTTPException(status_code=404, detail=f"Annotation '{annotation_id}' not found.")
    return ann.to_dict()


@router.post("/{annotation_id}/relationships", status_code=201)
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


@router.get("/about/{entity_id}", status_code=200)
def get_annotations_about_entity(
    entity_id: str,
    mgr: AnnotationManager = Depends(get_annotation_manager),
):
    results = mgr.get_annotations_about_entity(entity_id)
    return {"entity_id": entity_id, "annotations": results}


@router.post("/subgraph", status_code=200)
def get_annotation_subgraph(
    req: SubgraphRequest,
    mgr: AnnotationManager = Depends(get_annotation_manager),
):
    subgraph = mgr.get_annotation_subgraph(req.annotation_ids)
    return subgraph
