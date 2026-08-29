"""
Unit tests for Phase 1 — Shared Knowledge Graph Core.
"""

import pytest
from polaris_kg.core.kg import KnowledgeGraph
from polaris_kg.core.storage import InMemoryStorageEngine


def test_kg_node_crud():
    kg = KnowledgeGraph(InMemoryStorageEngine())

    # Create node
    node = kg.create_node(node_id="protein_x", label="Protein", properties={"name": "Protein X", "weight": 50})
    assert node.id == "protein_x"
    assert node.label == "Protein"
    assert node.properties["name"] == "Protein X"

    # Get node
    retrieved = kg.get_node("protein_x")
    assert retrieved is not None
    assert retrieved.properties["weight"] == 50

    # Update node
    updated = kg.update_node("protein_x", properties={"weight": 55, "status": "active"}, label="Enzyme")
    assert updated.label == "Enzyme"
    assert updated.properties["weight"] == 55
    assert updated.properties["status"] == "active"

    # Delete node
    assert kg.delete_node("protein_x") is True
    assert kg.get_node("protein_x") is None


def test_kg_relationships_and_collections():
    kg = KnowledgeGraph(InMemoryStorageEngine())

    n1 = kg.create_node(node_id="gene_a", label="Gene", properties={"name": "Gene A"})
    n2 = kg.create_node(node_id="protein_b", label="Protein", properties={"name": "Protein B"})

    rel = kg.create_relationship(source_id="gene_a", target_id="protein_b", type="encodes", rel_id="r1")
    assert rel.id == "r1"
    assert rel.source_id == "gene_a"
    assert rel.target_id == "protein_b"

    rels = kg.get_relationships(source_id="gene_a")
    assert len(rels) == 1
    assert rels[0].type == "encodes"

    # Collection
    coll = kg.create_collection(name="Genomics", collection_id="c1", description="Gene dataset")
    assert coll.id == "c1"
    assert kg.add_to_collection("c1", node_ids=["gene_a", "protein_b"], relationship_ids=["r1"]) is True

    fetched_coll = kg.get_collection("c1")
    assert "gene_a" in fetched_coll.node_ids
    assert "r1" in fetched_coll.relationship_ids


def test_kg_query_and_subgraph():
    kg = KnowledgeGraph(InMemoryStorageEngine())

    kg.create_node(node_id="n1", label="Disease", properties={"name": "Diabetes"})
    kg.create_node(node_id="n2", label="Disease", properties={"name": "Cancer"})
    kg.create_node(node_id="n3", label="Drug", properties={"name": "Metformin"})

    kg.create_relationship(source_id="n3", target_id="n1", type="treats")

    # Query
    results = kg.query({"label": "Disease"})
    assert len(results) == 2

    # Subgraph
    subgraph = kg.get_subgraph(node_ids=["n1"], depth=1)
    node_ids = {n.id for n in subgraph.nodes}
    assert "n1" in node_ids
    assert "n3" in node_ids
    assert len(subgraph.relationships) == 1
