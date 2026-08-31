"""
Annotation-Aware Multi-Perspective Retriever for KG Library.
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
import logging
from kg_library_api.core.kg import KnowledgeGraph
from kg_library_api.traversal.engine import DeterministicTraversalEngine, TraversalResult
from kg_library_api.annotations.manager import AnnotationManager
from kg_library_api.retrieval.packs import ToolManager

logger = logging.getLogger("kg_library_api.retrieval.retriever")


class RetrievalMode(str, Enum):
    BASE_KG_ONLY = "MODE_1_BASE_KG_ONLY"
    ANNOTATION_KG_ONLY = "MODE_2_ANNOTATION_KG_ONLY"
    HYBRID_BASE_AND_ANNOTATION = "MODE_3_BASE_AND_ANNOTATION"


@dataclass
class MultiPerspectiveSearchResult:
    """Contains multi-perspective search results maintaining logical separation."""
    mode: RetrievalMode
    knowledge_paths: List[Dict[str, Any]] = field(default_factory=list)
    annotations: List[Dict[str, Any]] = field(default_factory=list)
    annotation_paths: List[Dict[str, Any]] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    provenance: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode.value,
            "knowledge_paths": self.knowledge_paths,
            "annotations": self.annotations,
            "annotation_paths": self.annotation_paths,
            "evidence": self.evidence,
            "provenance": self.provenance,
        }


class AnnotationAwareRetriever:
    """
    Executes multi-perspective retrieval over Base Knowledge Graph and/or Expert Annotation Graph.
    Supports Mode 1 (Base KG), Mode 2 (Annotation KG), and Mode 3 (Base KG + Annotation KG).
    """

    def __init__(self, base_kg: KnowledgeGraph, annotation_mgr: AnnotationManager):
        self.base_kg = base_kg
        self.annotation_mgr = annotation_mgr
        self.traversal_engine = DeterministicTraversalEngine(base_kg)
        self.tool_manager = ToolManager()

    def retrieve(
        self,
        start_entity_ids: List[str],
        mode: RetrievalMode = RetrievalMode.HYBRID_BASE_AND_ANNOTATION,
        max_depth: int = 3,
        relationship_types: Optional[List[str]] = None,
        node_labels: Optional[List[str]] = None,
        traversal_mode: str = "manual",  # "manual" or "ai"
        llm: Optional[Any] = None,
        query: Optional[str] = None,
        enable_domain_packs: bool = True,
    ) -> MultiPerspectiveSearchResult:
        knowledge_paths = []
        annotations_list = []
        annotation_paths = []
        evidence_list = []
        provenance_list = []

        # MODE 1 or MODE 3: Retrieve Base KG paths via traversal engine
        if mode in (RetrievalMode.BASE_KG_ONLY, RetrievalMode.HYBRID_BASE_AND_ANNOTATION):
            traversal_res: TraversalResult = self.traversal_engine.traverse(
                start_nodes=start_entity_ids,
                algorithm="bfs",
                max_depth=max_depth,
                relationship_types=relationship_types,
                node_labels=node_labels,
                traversal_mode=traversal_mode,
                llm=llm,
            )
            for path in traversal_res.paths:
                knowledge_paths.append(path.to_dict())

        # MODE 2 or MODE 3: Retrieve Annotation Graph
        if mode in (RetrievalMode.ANNOTATION_KG_ONLY, RetrievalMode.HYBRID_BASE_AND_ANNOTATION):
            visited_entity_ids = set(start_entity_ids)
            if mode == RetrievalMode.HYBRID_BASE_AND_ANNOTATION and knowledge_paths:
                for kpath in knowledge_paths:
                    for node in kpath["nodes"]:
                        visited_entity_ids.add(node["id"])

            collected_ann_ids = set()
            collected_rel_ids = set()

            for eid in visited_entity_ids:
                anns_for_entity = self.annotation_mgr.get_annotations_about_entity(eid)
                for item in anns_for_entity:
                    ann_dict = item["annotation"]
                    rel_dict = item["relationship"]

                    if ann_dict["id"] not in collected_ann_ids:
                        collected_ann_ids.add(ann_dict["id"])
                        annotations_list.append(ann_dict)

                        if ann_dict.get("type") == "Evidence" or rel_dict.get("relation_type") == "SUPPORTS":
                            evidence_list.append({
                                "annotation_id": ann_dict["id"],
                                "content": ann_dict["content"],
                                "confidence": ann_dict["confidence"],
                                "target_entity": eid,
                            })

                        if ann_dict.get("provenance") or ann_dict.get("source"):
                            provenance_list.append({
                                "annotation_id": ann_dict["id"],
                                "source": ann_dict.get("source", ""),
                                "provenance": ann_dict.get("provenance", ""),
                                "author": ann_dict.get("author", ""),
                            })

                    if rel_dict["id"] not in collected_rel_ids:
                        collected_rel_ids.add(rel_dict["id"])
                        annotation_paths.append({
                            "source_annotation": ann_dict["id"],
                            "relation_type": rel_dict["relation_type"],
                            "target_entity": eid,
                        })

            # Retrieve connected annotation-to-annotation subgraphs
            if collected_ann_ids:
                ann_subgraph = self.annotation_mgr.get_annotation_subgraph(list(collected_ann_ids))
                for arel in ann_subgraph["relationships"]:
                    if arel.get("target_kind") == "ANNOTATION" and arel["id"] not in collected_rel_ids:
                        collected_rel_ids.add(arel["id"])
                        annotation_paths.append({
                            "source_annotation": arel["source_annotation_id"],
                            "relation_type": arel["relation_type"],
                            "target_annotation": arel["target_id"],
                        })

        # Execute Domain Packs Retrieval for External Evidence
        if enable_domain_packs:
            detected_nodes = [self.base_kg.get_node(nid) for nid in start_entity_ids if self.base_kg.get_node(nid)]
            detected_entities_dicts = [n.to_dict() for n in detected_nodes]
            q = query or (f"Query about {' '.join(start_entity_ids)}" if start_entity_ids else "General search query")
            routed_tools = self.tool_manager.route_query(q, detected_entities_dicts)
            for pack_name, tool in routed_tools:
                try:
                    payload = {"query": q}
                    pack_res = self.tool_manager.execute_tool(pack_name, tool.name, payload)
                    evidence_list.append({
                        "source_pack": pack_name,
                        "tool": tool.name,
                        "content": pack_res.content,
                        "confidence": pack_res.confidence,
                        "source": pack_res.source
                    })
                    provenance_list.append({
                        "source_pack": pack_name,
                        "source": pack_res.source,
                        "provenance": pack_res.provenance,
                        "confidence": pack_res.confidence
                    })
                except Exception as e:
                    logger.error(f"Error executing domain pack tool {pack_name}/{tool.name}: {e}")

        return MultiPerspectiveSearchResult(
            mode=mode,
            knowledge_paths=knowledge_paths,
            annotations=annotations_list,
            annotation_paths=annotation_paths,
            evidence=evidence_list,
            provenance=provenance_list,
        )
