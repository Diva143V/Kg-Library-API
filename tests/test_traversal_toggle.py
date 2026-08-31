"""
Unit tests for Traversal Mode Toggle ('manual' vs 'ai').
"""

import pytest
from kg_library_api.core.kg import KnowledgeGraph
from kg_library_api.core.storage import InMemoryStorageEngine
from kg_library_api.annotations.manager import AnnotationManager
from kg_library_api.traversal.engine import DeterministicTraversalEngine
from kg_library_api.tog.worker import ToGWorker


def test_traversal_mode_toggle_engine():
    kg = KnowledgeGraph(InMemoryStorageEngine())
    kg.create_node("n1", label="Gene")
    kg.create_node("n2", label="Protein")
    kg.create_relationship("n1", "n2", type="encodes")

    engine = DeterministicTraversalEngine(kg)

    # Manual mode (deterministic code traversal)
    res_manual = engine.traverse(start_nodes=["n1"], traversal_mode="manual")
    assert res_manual.nodes_count == 2
    assert len(res_manual.paths) == 1

    # AI mode (LLM-driven candidate selection traversal)
    res_ai = engine.traverse(start_nodes=["n1"], traversal_mode="ai")
    assert res_ai.nodes_count == 2
    assert len(res_ai.paths) == 1


def test_tog_worker_traversal_mode_toggle():
    kg = KnowledgeGraph(InMemoryStorageEngine())
    ann_mgr = AnnotationManager(kg)

    kg.create_node("n1", label="Gene", properties={"name": "Gene 1"})
    kg.create_node("n2", label="Protein", properties={"name": "Protein 2"})
    kg.create_relationship("n1", "n2", type="encodes")

    worker = ToGWorker(kg, ann_mgr)

    # Test Manual mode execution
    res_manual = worker.execute_query("Query", start_entities=["n1"], traversal_mode="manual")
    assert "answer" in res_manual
    assert len(res_manual["knowledge_paths"]) == 1

    # Test AI mode execution
    res_ai = worker.execute_query("Query", start_entities=["n1"], traversal_mode="ai")
    assert "answer" in res_ai
    assert len(res_ai["knowledge_paths"]) == 1
