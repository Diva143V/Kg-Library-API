"""
Unit and integration tests for Polaris Domain Packs framework.
"""

import pytest
from fastapi.testclient import TestClient
from kg_library_api import KnowledgeGraph, InMemoryStorageEngine, AnnotationManager, ToGWorker, kg_library_api_app
from kg_library_api.retrieval.packs import ToolManager, DomainPackManifest, ToolDefinition


def test_tool_manager_registration_and_listing():
    tm = ToolManager()
    packs = tm.list_packs()
    assert len(packs) >= 4  # WebPack, BioMCP, OpenBB, CourtListener
    pack_names = [p["name"] for p in packs]
    assert "WebPack" in pack_names
    assert "BioMCP" in pack_names
    assert "OpenBB" in pack_names
    assert "CourtListener" in pack_names


def test_query_routing():
    tm = ToolManager()

    # Case 1: Query contains biological concepts
    routed = tm.route_query("Find mutation on gene BRCA1", [{"id": "g1", "label": "Gene"}])
    assert len(routed) > 0
    # BioMCP should be routed/prioritized due to entity or keywords
    assert routed[0][0] == "BioMCP"

    # Case 2: Query contains financial keywords
    routed = tm.route_query("Querying stock price for Apple", [{"id": "stock_apple", "label": "Stock"}])
    assert len(routed) > 0
    assert routed[0][0] == "OpenBB"

    # Case 3: Query contains legal keywords
    routed = tm.route_query("docket lookup for Supreme Court citation", [])
    assert len(routed) > 0
    assert routed[0][0] == "CourtListener"

    # Case 4: No matches, should fallback to WebPack
    routed = tm.route_query("Random unknown topic query", [])
    assert len(routed) == 1
    assert routed[0][0] == "WebPack"


def test_tool_execution():
    tm = ToolManager()

    # HTTP search tool (WebPack)
    res_web = tm.execute_tool("WebPack", "search", {"query": "Polaris design principles"})
    assert "Mocked web search result" in res_web.content
    assert res_web.confidence == 0.8

    # MCP tool (BioMCP)
    res_bio = tm.execute_tool("BioMCP", "query_biomcp", {"query": "BRCA1"})
    assert "BioMCP result" in res_bio.content
    assert "PubMed / ClinVar" in res_bio.source

    # MCP tool (OpenBB)
    res_fin = tm.execute_tool("OpenBB", "query_finance", {"query": "Index growth"})
    assert "OpenBB result" in res_fin.content

    # MCP tool (CourtListener)
    res_law = tm.execute_tool("CourtListener", "query_legal", {"query": "Case details"})
    assert "CourtListener result" in res_law.content


def test_tog_worker_domain_packs_integration():
    kg = KnowledgeGraph(InMemoryStorageEngine())
    ann_mgr = AnnotationManager(kg)

    kg.create_node("gene_brca1", label="Gene", properties={"name": "BRCA1"})
    kg.create_node("breast_cancer", label="Disease", properties={"name": "Breast Cancer"})
    kg.create_relationship("gene_brca1", "breast_cancer", type="implicated_in")

    worker = ToGWorker(kg, ann_mgr)
    res = worker.execute_query(
        query="Tell me about BRCA1 gene mutation.",
        include_annotations=True,
        start_entities=["gene_brca1"],
    )

    # Ensure evidence from BioMCP (routed because of the gene/disease entities/query) is included
    assert len(res["evidence"]) > 0
    evidence_packs = [ev.get("source_pack") for ev in res["evidence"] if "source_pack" in ev]
    assert "BioMCP" in evidence_packs or "WebPack" in evidence_packs


def test_api_endpoints_for_packs():
    # Use context manager so FastAPI lifespan runs and app.state is populated
    with TestClient(kg_library_api_app) as client:
        # Test GET /v1/tog/packs
        resp_list = client.get("/v1/tog/packs")
        assert resp_list.status_code == 200
        packs = resp_list.json()
        assert len(packs) >= 4

        # Test POST /v1/tog/packs/query
        resp_query = client.post(
            "/v1/tog/packs/query",
            json={
                "pack_name": "BioMCP",
                "tool_name": "query_biomcp",
                "payload": {"query": "BRCA1"}
            }
        )
        assert resp_query.status_code == 200
        data = resp_query.json()
        assert "content" in data
        assert "PubMed" in data["source"]
