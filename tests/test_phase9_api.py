"""
Phase 9 — Full HTTP/API Interface Verification Suite.
"""

import pytest
from fastapi.testclient import TestClient
from polaris_kg.api.app import app
from polaris_kg.api.annotation_router import get_annotation_manager
from polaris_kg.api.tog_router import get_tog_worker
from polaris_kg.core.kg import KnowledgeGraph
from polaris_kg.core.storage import InMemoryStorageEngine
from polaris_kg.annotations.manager import AnnotationManager
from polaris_kg.tog.worker import ToGWorker


@pytest.fixture
def api_client():
    kg = KnowledgeGraph(InMemoryStorageEngine())
    ann_mgr = AnnotationManager(kg)

    # Seed base KG data
    kg.create_node("Protein_X", label="Protein", properties={"name": "Protein X"})
    kg.create_node("Disease_Y", label="Disease", properties={"name": "Disease Y"})
    kg.create_relationship("Protein_X", "Disease_Y", type="associated_with", rel_id="rel_xy")

    worker = ToGWorker(kg, ann_mgr)

    app.dependency_overrides[get_annotation_manager] = lambda: ann_mgr
    app.dependency_overrides[get_tog_worker] = lambda: worker

    return TestClient(app)


def test_api_health(api_client):
    res = api_client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_phase9_full_api_workflow(api_client):
    # 1. Create collection
    res_coll = api_client.post("/annotations/collections", json={
        "name": "Expert Oncology Annotations",
        "description": "Curated set for oncology targets",
        "collection_id": "coll_oncology",
    })
    assert res_coll.status_code == 201
    assert res_coll.json()["id"] == "coll_oncology"

    # 2. Bulk annotation upload
    res_bulk = api_client.post("/annotations/collections/coll_oncology/bulk", json={
        "annotations": [
            {
                "id": "ann_e1",
                "type": "Evidence",
                "content": "Phase II clinical trial confirms Protein X downregulation mitigates Disease Y.",
                "author": "Dr. Diwakar",
                "confidence": 0.96,
                "source": "DOI:10.1038/s41586-024-00001",
                "provenance": "Nature 2024",
            },
            {
                "id": "ann_h1",
                "type": "Hypothesis",
                "content": "Protein X may interact with secondary receptor Z.",
                "author": "Dr. Diwakar",
            }
        ],
        "relationships": [
            {
                "source_annotation_id": "ann_e1",
                "target_id": "Protein_X",
                "target_kind": "KG_NODE",
                "relation_type": "ABOUT",
            },
            {
                "source_annotation_id": "ann_e1",
                "target_id": "Disease_Y",
                "target_kind": "KG_NODE",
                "relation_type": "SUPPORTS",
            },
            {
                "source_annotation_id": "ann_h1",
                "target_id": "ann_e1",
                "target_kind": "ANNOTATION",
                "relation_type": "REFERS",
            }
        ]
    })
    assert res_bulk.status_code == 200
    assert res_bulk.json()["annotations_ingested"] == 2
    assert res_bulk.json()["relationships_ingested"] == 3

    # 3. Annotation retrieval
    res_get = api_client.get("/annotations/ann_e1")
    assert res_get.status_code == 200
    assert res_get.json()["author"] == "Dr. Diwakar"

    # 4. Add individual annotation relationship
    res_rel = api_client.post("/annotations/ann_h1/relationships", json={
        "target_id": "Protein_X",
        "relation_type": "PROPOSES",
        "target_kind": "KG_NODE",
    })
    assert res_rel.status_code == 201

    # 5. Annotation retrieval about entity (KG query)
    res_about = api_client.get("/annotations/about/Protein_X")
    assert res_about.status_code == 200
    assert len(res_about.json()["annotations"]) >= 1

    # 6. Subgraph retrieval
    res_subgraph = api_client.post("/annotations/subgraph", json={
        "annotation_ids": ["ann_h1"]
    })
    assert res_subgraph.status_code == 200
    assert len(res_subgraph.json()["annotations"]) == 2

    # 7. ToG query
    res_tog = api_client.post("/tog/query", json={
        "query": "What evidence supports the relationship between Protein X and Disease Y?",
        "include_annotations": True,
        "max_depth": 3,
        "start_entities": ["Protein_X"],
    })
    assert res_tog.status_code == 200
    tog_data = res_tog.json()
    assert "answer" in tog_data
    assert len(tog_data["knowledge_paths"]) > 0
    assert len(tog_data["annotations"]) >= 1
    assert len(tog_data["evidence"]) >= 1
    assert tog_data["metadata"]["nodes_traversed"] >= 2
