"""
Unit tests for Phase 5 — Annotation-Aware Multi-Perspective Retrieval.
"""

import pytest
from kg_library_api.core.kg import KnowledgeGraph
from kg_library_api.core.storage import InMemoryStorageEngine
from kg_library_api.annotations.manager import AnnotationManager
from kg_library_api.retrieval.retriever import AnnotationAwareRetriever, RetrievalMode


def build_test_environment():
    base_kg = KnowledgeGraph(InMemoryStorageEngine())
    ann_mgr = AnnotationManager(base_kg)

    base_kg.create_node("gene_a", label="Gene")
    base_kg.create_node("protein_b", label="Protein")
    base_kg.create_relationship("gene_a", "protein_b", type="encodes")

    ann = ann_mgr.create_annotation(
        annotation_id="ann_b",
        type="Evidence",
        content="Protein B verified by Western Blot.",
        source="LabReport#123",
    )
    ann_mgr.add_annotation_relationship("ann_b", "protein_b", relation_type="ABOUT")

    return base_kg, ann_mgr


def test_retrieval_mode_1_base_kg_only():
    base_kg, ann_mgr = build_test_environment()
    retriever = AnnotationAwareRetriever(base_kg, ann_mgr)

    res = retriever.retrieve(["gene_a"], mode=RetrievalMode.BASE_KG_ONLY)
    assert len(res.knowledge_paths) > 0
    assert len(res.annotations) == 0
    assert len(res.annotation_paths) == 0


def test_retrieval_mode_2_annotation_kg_only():
    base_kg, ann_mgr = build_test_environment()
    retriever = AnnotationAwareRetriever(base_kg, ann_mgr)

    res = retriever.retrieve(["protein_b"], mode=RetrievalMode.ANNOTATION_KG_ONLY)
    assert len(res.knowledge_paths) == 0
    assert len(res.annotations) == 1
    assert res.annotations[0]["id"] == "ann_b"


def test_retrieval_mode_3_hybrid_base_and_annotation():
    base_kg, ann_mgr = build_test_environment()
    retriever = AnnotationAwareRetriever(base_kg, ann_mgr)

    res = retriever.retrieve(["gene_a"], mode=RetrievalMode.HYBRID_BASE_AND_ANNOTATION)
    assert len(res.knowledge_paths) > 0
    assert len(res.annotations) == 1
    assert len(res.annotation_paths) == 1
