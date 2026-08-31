"""
Unit tests for Phase 4 — Knowledge-Graph Annotation API Endpoints.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from kg_library_api.api.annotation_router import router, get_annotation_manager
from kg_library_api.annotations.manager import AnnotationManager

app = FastAPI()
app.include_router(router, prefix="/v1")


@pytest.fixture
def client():
    # Fresh manager per test
    fresh_mgr = AnnotationManager()
    app.dependency_overrides[get_annotation_manager] = lambda: fresh_mgr
    return TestClient(app)


def test_annotation_api_full_flow(client):
    # 1. Create Collection
    res_coll = client.post("/v1/annotations/collections", json={"name": "Genomics Annotations", "description": "Expert curation"})
    assert res_coll.status_code == 201
    coll_id = res_coll.json()["id"]

    # 2. Add individual annotation
    res_ann = client.post("/v1/annotations", json={
        "annotation_id": "ann_101",
        "type": "Evidence",
        "content": "Binding affinity Kd = 5 nM.",
        "author": "BioCurator",
        "confidence": 0.98,
    })
    assert res_ann.status_code == 201
    assert res_ann.json()["id"] == "ann_101"

    # 3. Get annotation
    res_get = client.get("/v1/annotations/ann_101")
    assert res_get.status_code == 200
    assert res_get.json()["type"] == "Evidence"

    # 4. Add relationship (ann_101 ABOUT protein_y)
    res_rel = client.post("/v1/annotations/ann_101/relationships", json={
        "target_id": "protein_y",
        "relation_type": "ABOUT",
        "target_kind": "KG_NODE",
    })
    assert res_rel.status_code == 201
    assert res_rel.json()["relation_type"] == "ABOUT"

    # 5. Get annotations about protein_y
    res_about = client.get("/v1/annotations/about/protein_y")
    assert res_about.status_code == 200
    assert len(res_about.json()["annotations"]) == 1

    # 6. Bulk Ingest
    res_bulk = client.post(f"/v1/annotations/collections/{coll_id}/bulk", json={
        "annotations": [
            {"annotation_id": "b1", "type": "Hypothesis", "content": "Protein Y targets Disease Z."},
            {"annotation_id": "b2", "type": "Assertion", "content": "Confirmed by assay."},
        ],
        "relationships": [
            {"relationship_id": "r1", "source_annotation_id": "b2", "target_id": "b1", "relation_type": "SUPPORTS", "target_kind": "ANNOTATION"}
        ]
    })
    assert res_bulk.status_code == 200
    assert res_bulk.json()["annotations_ingested"] == 2

    # Verify annotation lookup works with these ids
    res_get_b1 = client.get("/v1/annotations/b1")
    assert res_get_b1.status_code == 200
    assert res_get_b1.json()["content"] == "Protein Y targets Disease Z."

    # 7. Annotation Subgraph
    res_subgraph = client.post("/v1/annotations/subgraph", json={"annotation_ids": ["b1"]})
    assert res_subgraph.status_code == 200
    assert len(res_subgraph.json()["annotations"]) == 2
