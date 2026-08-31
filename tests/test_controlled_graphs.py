"""
Controlled Graph Verification Suite for Phase 8 (TEST A, TEST B, TEST C, TEST D).
"""

import pytest
from kg_library_api.core.kg import KnowledgeGraph
from kg_library_api.core.storage import InMemoryStorageEngine
from kg_library_api.traversal.engine import DeterministicTraversalEngine
from kg_library_api.annotations.models import AnnotationType, AnnotationToKGRelationType
from kg_library_api.annotations.manager import AnnotationManager
from kg_library_api.retrieval.retriever import AnnotationAwareRetriever, RetrievalMode
from kg_library_api.tog.worker import ToGWorker


def test_controlled_graph_a():
    """
    TEST A:
    Gene A --encodes--> Protein B --associated_with--> Disease C
    Verify: node creation, relationship creation, BFS, DFS, k-hop, path extraction, subgraph extraction.
    """
    kg = KnowledgeGraph(InMemoryStorageEngine())

    n_gene = kg.create_node("Gene_A", label="Gene", properties={"symbol": "GA"})
    n_prot = kg.create_node("Protein_B", label="Protein", properties={"symbol": "PB"})
    n_dis = kg.create_node("Disease_C", label="Disease", properties={"name": "Condition C"})

    rel1 = kg.create_relationship("Gene_A", "Protein_B", type="encodes", rel_id="rel_encodes")
    rel2 = kg.create_relationship("Protein_B", "Disease_C", type="associated_with", rel_id="rel_assoc")

    assert kg.get_node("Gene_A") is not None
    assert kg.get_node("Protein_B") is not None
    assert kg.get_node("Disease_C") is not None

    engine = DeterministicTraversalEngine(kg)

    # BFS
    res_bfs = engine.bfs(["Gene_A"], max_depth=2)
    assert res_bfs.nodes_count == 3
    assert len(res_bfs.paths) >= 2

    # DFS
    res_dfs = engine.dfs(["Gene_A"], max_depth=2)
    assert res_dfs.nodes_count == 3

    # k-hop
    res_khop = engine.k_hop(["Gene_A"], k=2)
    assert res_khop.nodes_count == 3

    # Subgraph extraction
    subgraph = kg.get_subgraph(["Gene_A"], depth=2)
    assert len(subgraph.nodes) == 3
    assert len(subgraph.relationships) == 2


def test_controlled_graph_b():
    """
    TEST B:
    Annotation A --ABOUT--> Protein B
    Annotation A --SUPPORTS--> Disease C
    Verify: annotation creation, collection, annotation -> KG relationship, annotation retrieval.
    """
    kg = KnowledgeGraph(InMemoryStorageEngine())
    ann_mgr = AnnotationManager(kg)

    kg.create_node("Protein_B", label="Protein")
    kg.create_node("Disease_C", label="Disease")

    ann_a = ann_mgr.create_annotation(
        annotation_id="Annotation_A",
        type=AnnotationType.EVIDENCE.value,
        content="Published assay confirms Protein B role in Disease C.",
        author="Expert X",
        source="DOI:10.1000/182",
    )

    coll = ann_mgr.create_annotation_collection("Curation_Set_1", collection_id="coll_1")
    ann_mgr.add_annotation_relationship("Annotation_A", "Protein_B", relation_type="ABOUT")
    ann_mgr.add_annotation_relationship("Annotation_A", "Disease_C", relation_type="SUPPORTS")

    about_b = ann_mgr.get_annotations_about_entity("Protein_B")
    assert len(about_b) == 1
    assert about_b[0]["annotation"]["id"] == "Annotation_A"

    about_c = ann_mgr.get_annotations_about_entity("Disease_C")
    assert len(about_c) == 1
    assert about_c[0]["relationship"]["relation_type"] == "SUPPORTS"


def test_controlled_graph_c():
    """
    TEST C:
    Annotation A --SUPPORTS--> Disease C
    Annotation B --CONTRADICTS--> Disease C
    Verify: conflicting annotations, annotation traversal, provenance, separate support/contradiction results.
    """
    kg = KnowledgeGraph(InMemoryStorageEngine())
    ann_mgr = AnnotationManager(kg)

    kg.create_node("Disease_C", label="Disease")

    ann_a = ann_mgr.create_annotation(
        annotation_id="Annotation_A",
        type=AnnotationType.EVIDENCE.value,
        content="Study A shows positive therapeutic correlation.",
        provenance="Study A 2024",
    )

    ann_b = ann_mgr.create_annotation(
        annotation_id="Annotation_B",
        type=AnnotationType.OBSERVATION.value,
        content="Study B failed to replicate therapeutic effect.",
        provenance="Study B 2025",
    )

    ann_mgr.add_annotation_relationship("Annotation_A", "Disease_C", relation_type="SUPPORTS")
    ann_mgr.add_annotation_relationship("Annotation_B", "Disease_C", relation_type="CONTRADICTS")

    anns_c = ann_mgr.get_annotations_about_entity("Disease_C")
    assert len(anns_c) == 2

    rel_types = [item["relationship"]["relation_type"] for item in anns_c]
    assert "SUPPORTS" in rel_types
    assert "CONTRADICTS" in rel_types

    provenance_sources = [item["annotation"]["provenance"] for item in anns_c]
    assert "Study A 2024" in provenance_sources
    assert "Study B 2025" in provenance_sources


def test_controlled_graph_d_tog():
    """
    TEST D — ToG:
    Query: "What evidence supports the relationship between Protein B and Disease C?"
    Verify: expected result must contain:
    - relevant KG relationship
    - relevant annotation
    - annotation relationship
    - provenance
    - reasoning result
    """
    kg = KnowledgeGraph(InMemoryStorageEngine())
    ann_mgr = AnnotationManager(kg)

    kg.create_node("Protein_B", label="Protein", properties={"name": "Protein B"})
    kg.create_node("Disease_C", label="Disease", properties={"name": "Disease C"})
    kg.create_relationship("Protein_B", "Disease_C", type="associated_with", rel_id="rel_bc")

    ann = ann_mgr.create_annotation(
        annotation_id="Ann_Evidence_1",
        type="Evidence",
        content="High-throughput screening confirms binding of Protein B to Disease C pathway target.",
        source="DOI:10.1016/j.cell.2024",
        provenance="Cell Journal 2024",
    )
    ann_mgr.add_annotation_relationship("Ann_Evidence_1", "Protein_B", relation_type="ABOUT")
    ann_mgr.add_annotation_relationship("Ann_Evidence_1", "Disease_C", relation_type="SUPPORTS")

    worker = ToGWorker(kg, ann_mgr)
    query_str = "What evidence supports the relationship between Protein B and Disease C?"
    res = worker.execute_query(query=query_str, include_annotations=True, max_depth=2, start_entities=["Protein_B"])

    # 1. Relevant KG relationship
    assert len(res["knowledge_paths"]) > 0
    rel_types_in_paths = [r["type"] for p in res["knowledge_paths"] for r in p["relationships"]]
    assert "associated_with" in rel_types_in_paths

    # 2. Relevant annotation
    ann_ids = [a["id"] for a in res["annotations"]]
    assert "Ann_Evidence_1" in ann_ids

    # 3. Annotation relationship
    assert len(res["annotation_paths"]) >= 2

    # 4. Provenance
    prov_sources = [p["source"] for p in res["provenance"]]
    assert "DOI:10.1016/j.cell.2024" in prov_sources

    # 5. Reasoning result
    assert "answer" in res
    assert len(res["answer"]) > 0
