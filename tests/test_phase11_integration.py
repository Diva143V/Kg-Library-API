"""
Phase 11 — Polaris Integration Verification Suite.
"""

import pytest
from kg_library_api import (
    KnowledgeGraph,
    InMemoryStorageEngine,
    AnnotationManager,
    AnnotationType,
    DeterministicTraversalEngine,
    AnnotationAwareRetriever,
    RetrievalMode,
    ToGWorker,
    kg_library_api_app,
)
from fastapi.testclient import TestClient


def test_polaris_public_exports():
    assert KnowledgeGraph is not None
    assert AnnotationManager is not None
    assert ToGWorker is not None
    assert kg_library_api_app is not None


def test_polaris_full_end_to_end_pipeline():
    # 1. Initialize Core KG & Storage
    kg = KnowledgeGraph(InMemoryStorageEngine())

    # Create Base Knowledge
    g1 = kg.create_node("Gene_1", label="Gene", properties={"name": "BRCA1"})
    p1 = kg.create_node("Protein_1", label="Protein", properties={"name": "BRCA1 Protein"})
    d1 = kg.create_node("Disease_1", label="Disease", properties={"name": "Breast Cancer"})

    kg.create_relationship("Gene_1", "Protein_1", type="encodes")
    kg.create_relationship("Protein_1", "Disease_1", type="associated_with")

    # 2. Initialize Expert Annotation Manager
    ann_mgr = AnnotationManager(kg)
    ann1 = ann_mgr.create_annotation(
        annotation_id="ann_expert_1",
        type=AnnotationType.EVIDENCE.value,
        content="Pathogenic variant confirmed in clinical cohort.",
        author="Geneticist A",
        confidence=0.99,
        provenance="ClinVar:2024",
    )
    ann_mgr.add_annotation_relationship("ann_expert_1", "Protein_1", relation_type="ABOUT")
    ann_mgr.add_annotation_relationship("ann_expert_1", "Disease_1", relation_type="SUPPORTS")

    # 3. Deterministic Traversal Engine
    traversal_engine = DeterministicTraversalEngine(kg)
    traversal_res = traversal_engine.bfs(["Gene_1"], max_depth=2)
    assert traversal_res.nodes_count == 3

    # 4. Multi-Perspective Retrieval
    retriever = AnnotationAwareRetriever(kg, ann_mgr)
    multi_res = retriever.retrieve(["Gene_1"], mode=RetrievalMode.HYBRID_BASE_AND_ANNOTATION)
    assert len(multi_res.knowledge_paths) > 0
    assert len(multi_res.annotations) == 1

    # 5. Think-on-Graph Worker
    worker = ToGWorker(kg, ann_mgr)
    tog_res = worker.execute_query(
        query="What evidence supports the relationship between BRCA1 and Breast Cancer?",
        include_annotations=True,
        max_depth=3,
        start_entities=["Gene_1"],
    )

    assert "answer" in tog_res
    assert len(tog_res["knowledge_paths"]) > 0
    assert len(tog_res["annotations"]) == 1
    assert tog_res["metadata"]["nodes_traversed"] >= 3

    # 6. HTTP API Interface
    client = TestClient(kg_library_api_app)
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "ok"
