"""
Integration tests for Polaris SQL Storage Engine and SQL Annotation persistence.
"""

import pytest
from kg_library_api.core.models import Node, Relationship, Collection
from kg_library_api.core.storage import SQLStorageEngine
from kg_library_api.core.kg import KnowledgeGraph
from kg_library_api.annotations.db_manager import SQLAnnotationStorage
from kg_library_api.annotations.manager import AnnotationManager
from kg_library_api.tog.worker import ToGWorker


def test_sql_storage_engine_crud():
    # SQLite in-memory database URL
    db_url = "sqlite:///:memory:"

    # 1. Initialize SQL Storage Engine
    storage = SQLStorageEngine(db_url)
    kg = KnowledgeGraph(storage)

    # Verify CRUD on Nodes
    node1 = Node(id="N_1", label="Protein", properties={"name": "TP53"})
    kg.create_node(node1.id, node1.label, node1.properties)

    fetched_node = kg.get_node("N_1")
    assert fetched_node is not None
    assert fetched_node.label == "Protein"
    assert fetched_node.properties["name"] == "TP53"

    # Update Node
    kg.update_node("N_1", {"function": "Tumor Suppressor"}, label="TumorProtein")
    updated = kg.get_node("N_1")
    assert updated.label == "TumorProtein"
    assert updated.properties["name"] == "TP53"
    assert updated.properties["function"] == "Tumor Suppressor"

    # Create target node
    node2 = Node(id="N_2", label="Disease", properties={"name": "Cancer"})
    kg.create_node(node2.id, node2.label, node2.properties)

    # Verify CRUD on Relationships
    rel = Relationship(id="R_1", source_id="N_1", target_id="N_2", type="associated_with", properties={"evidence": "strong"})
    kg.create_relationship(rel.source_id, rel.target_id, rel.type, rel.id, rel.properties)

    fetched_rels = kg.get_relationships(source_id="N_1")
    assert len(fetched_rels) == 1
    assert fetched_rels[0].id == "R_1"
    assert fetched_rels[0].properties["evidence"] == "strong"

    # Verify Collections
    coll = Collection(id="C_1", name="Tumor Set", description="Subset of oncology elements")
    kg.create_collection(coll.name, coll.id, coll.description)
    kg.add_to_collection("C_1", ["N_1", "N_2"], ["R_1"])

    fetched_coll = kg.get_collection("C_1")
    assert fetched_coll is not None
    assert "N_1" in fetched_coll.node_ids
    assert "R_1" in fetched_coll.relationship_ids

    # Query Filters
    query_res = kg.query({"label": "TumorProtein"})
    assert len(query_res) == 1
    assert query_res[0].id == "N_1"

    # Subgraph extraction
    subgraph = kg.get_subgraph(["N_1"], depth=1)
    assert len(subgraph.nodes) == 2
    assert len(subgraph.relationships) == 1

    # Delete Node
    kg.delete_node("N_1")
    assert kg.get_node("N_1") is None
    # Relationships linked to N_1 should also be deleted
    assert len(kg.get_relationships(source_id="N_1")) == 0


def test_sql_annotation_persistence():
    db_url = "sqlite:///:memory:"

    kg_storage = SQLStorageEngine(db_url)
    kg = KnowledgeGraph(kg_storage)
    
    ann_storage = SQLAnnotationStorage(db_url)
    ann_mgr = AnnotationManager(kg, db_storage=ann_storage)

    # Create nodes
    kg.create_node("Gene_A", label="Gene")
    kg.create_node("Disease_B", label="Disease")

    # Create expert annotations
    ann = ann_mgr.create_annotation(
        type="Evidence",
        content="Supports correlation between Gene_A and Disease_B.",
        author="Expert Oncologist",
        confidence=0.95
    )

    # Link annotation to nodes
    ann_mgr.add_annotation_relationship(ann.id, "Gene_A", relation_type="ABOUT")
    ann_mgr.add_annotation_relationship(ann.id, "Disease_B", relation_type="SUPPORTS")

    # Query annotations about entity
    results = ann_mgr.get_annotations_about_entity("Gene_A")
    assert len(results) == 1
    assert results[0]["annotation"]["id"] == ann.id
    assert results[0]["relationship"]["relation_type"] == "ABOUT"

    # Annotation Subgraph extraction
    subgraph = ann_mgr.get_annotation_subgraph([ann.id])
    assert len(subgraph["annotations"]) == 1
    assert subgraph["annotations"][0]["id"] == ann.id
