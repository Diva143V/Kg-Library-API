"""
Domain-agnostic Graph CRUD API.
Provides full create/read/update/delete operations on nodes, relationships,
collections, and subgraphs — with pagination on all list endpoints.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from kg_library_api.core.kg import KnowledgeGraph

router = APIRouter(prefix="/graph", tags=["Graph"])


# ── Dependency ─────────────────────────────────────────────────────────────────

def get_kg(request: Request) -> KnowledgeGraph:
    return request.app.state.kg


# ── Request / Response schemas ─────────────────────────────────────────────────

class CreateNodeRequest(BaseModel):
    label: str = Field(default="Node", description="Domain label for the node (e.g. 'Drug', 'Person', 'Concept')")
    node_id: Optional[str] = Field(default=None, description="Optional client-supplied ID; auto-generated if omitted")
    properties: Dict[str, Any] = Field(default_factory=dict)


class UpdateNodeRequest(BaseModel):
    properties: Dict[str, Any]
    label: Optional[str] = None


class CreateRelationshipRequest(BaseModel):
    source_id: str
    target_id: str
    type: str = Field(description="Relationship type (e.g. 'TREATS', 'KNOWS', 'DEPENDS_ON')")
    rel_id: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    directed: bool = True


class CreateCollectionRequest(BaseModel):
    name: str
    collection_id: Optional[str] = None
    description: str = ""
    node_ids: List[str] = Field(default_factory=list)
    relationship_ids: List[str] = Field(default_factory=list)


class AddToCollectionRequest(BaseModel):
    node_ids: List[str] = Field(default_factory=list)
    relationship_ids: List[str] = Field(default_factory=list)


class SubgraphRequest(BaseModel):
    node_ids: List[str]
    depth: int = Field(default=1, ge=1, le=10)


# ── Node endpoints ─────────────────────────────────────────────────────────────

@router.get("/nodes", status_code=200, summary="List all nodes (paginated)")
def list_nodes(
    skip: int = Query(default=0, ge=0, description="Number of nodes to skip"),
    limit: int = Query(default=100, ge=1, le=1000, description="Max nodes to return"),
    kg: KnowledgeGraph = Depends(get_kg),
):
    nodes = kg.storage.list_nodes(skip=skip, limit=limit)
    return {"nodes": [n.to_dict() for n in nodes], "skip": skip, "limit": limit}


@router.post("/nodes", status_code=201, summary="Create a node")
def create_node(req: CreateNodeRequest, kg: KnowledgeGraph = Depends(get_kg)):
    node = kg.create_node(
        node_id=req.node_id,
        label=req.label,
        properties=req.properties,
    )
    return node.to_dict()


@router.get("/nodes/{node_id}", status_code=200, summary="Get a node by ID")
def get_node(node_id: str, kg: KnowledgeGraph = Depends(get_kg)):
    node = kg.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")
    return node.to_dict()


@router.patch("/nodes/{node_id}", status_code=200, summary="Update a node's properties or label")
def update_node(node_id: str, req: UpdateNodeRequest, kg: KnowledgeGraph = Depends(get_kg)):
    node = kg.update_node(node_id, req.properties, req.label)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")
    return node.to_dict()


@router.delete("/nodes/{node_id}", status_code=200, summary="Delete a node (and its relationships)")
def delete_node(node_id: str, kg: KnowledgeGraph = Depends(get_kg)):
    deleted = kg.delete_node(node_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")
    return {"deleted": True, "node_id": node_id}


# ── Relationship endpoints ─────────────────────────────────────────────────────

@router.get("/relationships", status_code=200, summary="List relationships (paginated, filterable)")
def list_relationships(
    source_id: Optional[str] = Query(default=None),
    target_id: Optional[str] = Query(default=None),
    type: Optional[str] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    kg: KnowledgeGraph = Depends(get_kg),
):
    if source_id or target_id or type:
        rels = kg.get_relationships(source_id=source_id, target_id=target_id, relationship_type=type)
        rels = rels[skip: skip + limit]
    else:
        rels = kg.storage.list_relationships(skip=skip, limit=limit)
    return {"relationships": [r.to_dict() for r in rels], "skip": skip, "limit": limit}


@router.post("/relationships", status_code=201, summary="Create a relationship")
def create_relationship(req: CreateRelationshipRequest, kg: KnowledgeGraph = Depends(get_kg)):
    # Validate source/target exist
    if not kg.get_node(req.source_id):
        raise HTTPException(status_code=404, detail=f"Source node '{req.source_id}' not found.")
    if not kg.get_node(req.target_id):
        raise HTTPException(status_code=404, detail=f"Target node '{req.target_id}' not found.")
    rel = kg.create_relationship(
        source_id=req.source_id,
        target_id=req.target_id,
        type=req.type,
        rel_id=req.rel_id,
        properties=req.properties,
        directed=req.directed,
    )
    return rel.to_dict()


@router.delete("/relationships/{relationship_id}", status_code=200, summary="Delete a relationship")
def delete_relationship(relationship_id: str, kg: KnowledgeGraph = Depends(get_kg)):
    deleted = kg.storage.delete_relationship(relationship_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Relationship '{relationship_id}' not found.")
    return {"deleted": True, "relationship_id": relationship_id}


# ── Query / Subgraph endpoints ─────────────────────────────────────────────────

@router.get("/query", status_code=200, summary="Query nodes by label and/or property filters")
def query_nodes(
    label: Optional[str] = Query(default=None),
    query_text: Optional[str] = Query(default=None, alias="q"),
    kg: KnowledgeGraph = Depends(get_kg),
):
    filters: Dict[str, Any] = {}
    if label:
        filters["label"] = label
    if query_text:
        filters["query"] = query_text
    nodes = kg.query(filters)
    return {"nodes": [n.to_dict() for n in nodes]}


@router.post("/subgraph", status_code=200, summary="Extract a subgraph around given node IDs")
def get_subgraph(req: SubgraphRequest, kg: KnowledgeGraph = Depends(get_kg)):
    subgraph = kg.get_subgraph(req.node_ids, depth=req.depth)
    return subgraph.to_dict()


# ── Collection endpoints ───────────────────────────────────────────────────────

@router.post("/collections", status_code=201, summary="Create a collection")
def create_collection(req: CreateCollectionRequest, kg: KnowledgeGraph = Depends(get_kg)):
    coll = kg.create_collection(
        name=req.name,
        collection_id=req.collection_id,
        description=req.description,
        node_ids=req.node_ids,
        relationship_ids=req.relationship_ids,
    )
    return coll.to_dict()


@router.get("/collections/{collection_id}", status_code=200, summary="Get a collection by ID")
def get_collection(collection_id: str, kg: KnowledgeGraph = Depends(get_kg)):
    coll = kg.get_collection(collection_id)
    if not coll:
        raise HTTPException(status_code=404, detail=f"Collection '{collection_id}' not found.")
    return coll.to_dict()


@router.post("/collections/{collection_id}/add", status_code=200, summary="Add nodes/relationships to a collection")
def add_to_collection(collection_id: str, req: AddToCollectionRequest, kg: KnowledgeGraph = Depends(get_kg)):
    ok = kg.add_to_collection(
        collection_id=collection_id,
        node_ids=req.node_ids,
        relationship_ids=req.relationship_ids,
    )
    if not ok:
        raise HTTPException(status_code=404, detail=f"Collection '{collection_id}' not found.")
    return {"updated": True, "collection_id": collection_id}
