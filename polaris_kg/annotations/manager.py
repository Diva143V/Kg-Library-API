"""
Annotation Manager maintaining logical separation between Base Knowledge and Expert Annotations.
"""

from typing import Dict, Any, List, Optional
import uuid
from polaris_kg.annotations.models import (
    Annotation,
    AnnotationRelationship,
    AnnotationType,
    AnnotationToKGRelationType,
    AnnotationToAnnotationRelationType,
)
from polaris_kg.core.models import Collection, Subgraph, Node, Relationship
from polaris_kg.core.kg import KnowledgeGraph


class AnnotationManager:
    """
    Manages first-class annotations, annotation collections, and annotation-to-KG / annotation-to-annotation relationships.
    Maintains strict logical separation between Base Knowledge and Expert Annotation Knowledge.
    """

    def __init__(self, base_kg: Optional[KnowledgeGraph] = None):
        self.base_kg = base_kg
        self.annotations: Dict[str, Annotation] = {}
        self.relationships: Dict[str, AnnotationRelationship] = {}
        self.collections: Dict[str, Collection] = {}

    def create_annotation(
        self,
        type: str,
        content: str,
        annotation_id: Optional[str] = None,
        author: str = "expert",
        confidence: float = 1.0,
        source: str = "",
        provenance: str = "",
        status: str = "active",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Annotation:
        aid = annotation_id or str(uuid.uuid4())
        ann = Annotation(
            id=aid,
            type=type,
            content=content,
            author=author,
            confidence=confidence,
            source=source,
            provenance=provenance,
            status=status,
            metadata=metadata or {},
        )
        self.annotations[aid] = ann
        return ann

    def get_annotation(self, annotation_id: str) -> Optional[Annotation]:
        return self.annotations.get(annotation_id)

    def create_annotation_collection(
        self,
        name: str,
        collection_id: Optional[str] = None,
        description: str = "",
        annotation_ids: Optional[List[str]] = None,
    ) -> Collection:
        cid = collection_id or str(uuid.uuid4())
        aids = annotation_ids or []
        coll = Collection(
            id=cid,
            name=name,
            description=description,
            node_ids=aids,  # Stores annotation_ids in node_ids field
            relationship_ids=[],
        )
        self.collections[cid] = coll
        return coll

    def bulk_ingest_annotations(
        self,
        collection_id: str,
        annotations_data: List[Dict[str, Any]],
        relationships_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Bulk ingest a list of annotations into a collection."""
        coll = self.collections.get(collection_id)
        if not coll:
            coll = self.create_annotation_collection(name=f"Collection {collection_id}", collection_id=collection_id)

        created_anns = []
        for adata in annotations_data:
            ann = Annotation.from_dict(adata)
            self.annotations[ann.id] = ann
            if ann.id not in coll.node_ids:
                coll.node_ids.append(ann.id)
            created_anns.append(ann)

        created_rels = []
        if relationships_data:
            for rdata in relationships_data:
                rid = rdata.get("id") or str(uuid.uuid4())
                rel = AnnotationRelationship(
                    id=rid,
                    source_annotation_id=rdata["source_annotation_id"],
                    target_id=rdata["target_id"],
                    target_kind=rdata.get("target_kind", "KG_NODE"),
                    relation_type=rdata["relation_type"],
                    properties=rdata.get("properties", {}),
                )
                self.relationships[rel.id] = rel
                created_rels.append(rel)

        return {
            "collection_id": collection_id,
            "annotations_ingested": len(created_anns),
            "relationships_ingested": len(created_rels),
        }

    def add_annotation_relationship(
        self,
        source_annotation_id: str,
        target_id: str,
        relation_type: str,
        target_kind: str = "KG_NODE",
        relationship_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> AnnotationRelationship:
        rid = relationship_id or str(uuid.uuid4())
        rel = AnnotationRelationship(
            id=rid,
            source_annotation_id=source_annotation_id,
            target_id=target_id,
            target_kind=target_kind,
            relation_type=relation_type,
            properties=properties or {},
        )
        self.relationships[rid] = rel
        return rel

    def get_annotations_about_entity(self, entity_id: str) -> List[Dict[str, Any]]:
        """Retrieve all annotations associated with a specific KG node/entity."""
        results = []
        for rel in self.relationships.values():
            if rel.target_id == entity_id and rel.target_kind == "KG_NODE":
                ann = self.annotations.get(rel.source_annotation_id)
                if ann:
                    results.append({
                        "annotation": ann.to_dict(),
                        "relationship": rel.to_dict(),
                    })
        return results

    def get_annotation_subgraph(self, annotation_ids: List[str]) -> Dict[str, Any]:
        """Extract the connected subgraph of annotations and their relationships."""
        visited_anns = set()
        frontier = set(annotation_ids)
        collected_rel_ids = set()

        while frontier:
            next_frontier = set()
            for aid in frontier:
                if aid in visited_anns or aid not in self.annotations:
                    continue
                visited_anns.add(aid)

                for rel in self.relationships.values():
                    if rel.source_annotation_id == aid:
                        collected_rel_ids.add(rel.id)
                        if rel.target_kind == "ANNOTATION":
                            next_frontier.add(rel.target_id)
                    elif rel.target_id == aid and rel.target_kind == "ANNOTATION":
                        collected_rel_ids.add(rel.id)
                        next_frontier.add(rel.source_annotation_id)

            frontier = next_frontier

        anns_list = [self.annotations[aid].to_dict() for aid in visited_anns if aid in self.annotations]
        rels_list = [self.relationships[rid].to_dict() for rid in collected_rel_ids if rid in self.relationships]
        return {
            "annotations": anns_list,
            "relationships": rels_list,
        }
