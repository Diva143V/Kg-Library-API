"""
Unit tests for Phase 6 & Phase 7 — Think-on-Graph Worker & ToG Worker API.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from kg_library_api.core.kg import KnowledgeGraph
from kg_library_api.core.storage import InMemoryStorageEngine
from kg_library_api.annotations.manager import AnnotationManager
from kg_library_api.tog.worker import ToGWorker
from kg_library_api.api.tog_router import router as tog_router, get_tog_worker

app = FastAPI()
app.include_router(tog_router)


def build_tog_test_worker():
    kg = KnowledgeGraph(InMemoryStorageEngine())
    ann_mgr = AnnotationManager(kg)

    kg.create_node("protein_b", label="Protein", properties={"name": "Protein B"})
    kg.create_node("disease_c", label="Disease", properties={"name": "Disease C"})
    kg.create_relationship("protein_b", "disease_c", type="associated_with", rel_id="r1")

    ann = ann_mgr.create_annotation(
        annotation_id="ann_bc",
        type="Evidence",
        content="Evidence supports association between Protein B and Disease C.",
        provenance="PubMed:12345",
    )
    ann_mgr.add_annotation_relationship("ann_bc", "protein_b", relation_type="ABOUT")
    ann_mgr.add_annotation_relationship("ann_bc", "disease_c", relation_type="SUPPORTS")

    return ToGWorker(kg, ann_mgr)


def test_tog_worker_execution():
    worker = build_tog_test_worker()
    res = worker.execute_query(
        query="What evidence supports the relationship between Protein B and Disease C?",
        include_annotations=True,
        max_depth=3,
        start_entities=["protein_b"],
        enable_domain_packs=False,
    )

    assert "answer" in res
    assert len(res["knowledge_paths"]) > 0
    assert len(res["annotations"]) == 1
    assert len(res["evidence"]) == 1
    assert len(res["provenance"]) == 1
    assert res["metadata"]["nodes_traversed"] >= 2
    assert "latency_ms" in res["metadata"]


def test_tog_api_endpoint():
    worker = build_tog_test_worker()
    app.dependency_overrides[get_tog_worker] = lambda: worker
    client = TestClient(app)

    response = client.post(
        "/tog/query",
        json={
            "query": "What evidence supports the relationship between Protein B and Disease C?",
            "include_annotations": True,
            "max_depth": 3,
            "start_entities": ["protein_b"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "knowledge_paths" in data
    assert "annotations" in data
    assert "annotation_paths" in data
    assert "evidence" in data
    assert "provenance" in data
    assert "metadata" in data
    assert data["metadata"]["nodes_traversed"] >= 2
