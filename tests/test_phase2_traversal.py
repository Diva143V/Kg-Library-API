"""
Unit tests for Phase 2 — Deterministic Graph Traversal.
"""

import pytest
from polaris_kg.core.kg import KnowledgeGraph
from polaris_kg.core.storage import InMemoryStorageEngine
from polaris_kg.traversal.engine import DeterministicTraversalEngine


def build_sample_graph() -> KnowledgeGraph:
    kg = KnowledgeGraph(InMemoryStorageEngine())

    # Build Test Graph:
    # Gene A -> encodes -> Protein B -> associated_with -> Disease C
    # Protein B -> interacts_with -> Protein D
    kg.create_node("gene_a", label="Gene", properties={"name": "Gene A"})
    kg.create_node("protein_b", label="Protein", properties={"name": "Protein B"})
    kg.create_node("disease_c", label="Disease", properties={"name": "Disease C"})
    kg.create_node("protein_d", label="Protein", properties={"name": "Protein D"})

    kg.create_relationship("gene_a", "protein_b", type="encodes", rel_id="r1")
    kg.create_relationship("protein_b", "disease_c", type="associated_with", rel_id="r2")
    kg.create_relationship("protein_b", "protein_d", type="interacts_with", rel_id="r3")

    return kg


def test_bfs_traversal():
    kg = build_sample_graph()
    engine = DeterministicTraversalEngine(kg)

    res = engine.bfs(start_nodes=["gene_a"], max_depth=2)

    assert res.start_nodes == ["gene_a"]
    assert "gene_a" in res.visited_node_ids
    assert "protein_b" in res.visited_node_ids
    assert "disease_c" in res.visited_node_ids
    assert "protein_d" in res.visited_node_ids

    # Path from gene_a to disease_c
    path_targets = [[n.id for n in p.nodes] for p in res.paths]
    assert ["gene_a", "protein_b"] in path_targets
    assert ["gene_a", "protein_b", "disease_c"] in path_targets


def test_dfs_traversal():
    kg = build_sample_graph()
    engine = DeterministicTraversalEngine(kg)

    res = engine.dfs(start_nodes=["gene_a"], max_depth=2)
    assert res.nodes_count == 4
    assert len(res.paths) >= 3


def test_relationship_filtering_and_determinism():
    kg = build_sample_graph()
    engine = DeterministicTraversalEngine(kg)

    # Filter only 'encodes'
    res1 = engine.traverse(
        start_nodes=["gene_a"],
        algorithm="bfs",
        max_depth=3,
        relationship_types=["encodes"],
    )

    assert "protein_b" in res1.visited_node_ids
    assert "disease_c" not in res1.visited_node_ids

    # Test Determinism: run 5 times, confirm identical dict output
    runs = [
        engine.traverse(start_nodes=["gene_a"], algorithm="bfs", max_depth=3).to_dict()
        for _ in range(5)
    ]
    for r in runs[1:]:
        assert r == runs[0]
