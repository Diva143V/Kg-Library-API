"""
Integration tests for Polaris Hybrid ToG, AI Gateway, Escalation Gate, and Observability.
"""

import pytest
from kg_library_api import KnowledgeGraph, InMemoryStorageEngine, AnnotationManager, ToGWorker
from kg_library_api.ai import AIGateway, AIEscalationPolicy, MockAIProvider


def test_escalation_under_budget_and_limits():
    # 1. Setup Graph and Annotation Manager
    kg = KnowledgeGraph(InMemoryStorageEngine())
    ann_mgr = AnnotationManager(kg)

    kg.create_node("Gene_1", label="Gene")
    kg.create_node("Disease_1", label="Disease")
    kg.create_relationship("Gene_1", "Disease_1", type="associated_with")

    # Create conflicting expert evidence to trigger escalation gate
    ann_mgr.create_annotation(
        annotation_id="ann_1",
        type="Evidence",
        content="Positive evidence linking Gene 1 to Disease 1."
    )
    ann_mgr.add_annotation_relationship("ann_1", "Gene_1", relation_type="ABOUT")
    ann_mgr.add_annotation_relationship("ann_1", "Disease_1", relation_type="SUPPORTS")

    ann_mgr.create_annotation(
        annotation_id="ann_2",
        type="Evidence",
        content="Contradicting trial shows no significance."
    )
    ann_mgr.add_annotation_relationship("ann_2", "Gene_1", relation_type="ABOUT")
    ann_mgr.add_annotation_relationship("ann_2", "Disease_1", relation_type="CONTRADICTS")

    # 2. Setup AI Gateway with deterministic Mock Provider
    mock_provider = MockAIProvider(
        predefined_responses={
            "Gene_1": "In-depth semantic evaluation: Gene 1 shows conflict between ann_1 and ann_2."
        }
    )
    policy = AIEscalationPolicy(
        traversal_mode="hybrid",
        ai_enabled=True,
        max_ai_calls=2,
        ai_budget=0.05,
    )
    gateway = AIGateway(policy=policy, provider=mock_provider)

    worker = ToGWorker(kg, ann_mgr, ai_gateway=gateway)

    # 3. Execute Hybrid ToG Query
    res = worker.execute_query(
        query="What is the evidence regarding Gene_1 role in Disease_1?",
        traversal_mode="hybrid",
        enable_domain_packs=False,
    )

    # Check that AI was invoked and response populated
    assert res["metadata"]["ai_calls"] == 1
    assert "In-depth semantic evaluation" in res["answer"]
    assert "In-depth semantic evaluation" in res["perspectives"]["combined"]["details"]

    # Check Perspectives structure
    assert "knowledge" in res["perspectives"]
    assert "expert" in res["perspectives"]
    assert "combined" in res["perspectives"]

    # Check Observability Metadata
    meta = res["metadata"]
    assert meta["traversal_mode"] == "hybrid"
    assert meta["ai_calls"] == 1
    assert meta["actual_tokens"] > 0
    assert meta["estimated_tokens"] > 0
    assert meta["estimated_cost"] > 0.0
    assert meta["actual_cost"] > 0.0
    assert meta["escalation_reason"] == "conflicting_evidence"
    assert meta["budget_remaining"] < 0.05
    assert meta["python_traversal_ms"] >= 0


def test_escalation_budget_exhausted_fallback():
    kg = KnowledgeGraph(InMemoryStorageEngine())
    ann_mgr = AnnotationManager(kg)

    kg.create_node("Gene_1", label="Gene")
    kg.create_node("Disease_1", label="Disease")
    kg.create_relationship("Gene_1", "Disease_1", type="associated_with")

    # Conflicting annotations to trigger escalation gate
    ann_mgr.create_annotation(annotation_id="ann_1", type="Evidence", content="Supports")
    ann_mgr.add_annotation_relationship("ann_1", "Gene_1", relation_type="ABOUT")
    ann_mgr.add_annotation_relationship("ann_1", "Disease_1", relation_type="SUPPORTS")

    ann_mgr.create_annotation(annotation_id="ann_2", type="Evidence", content="Contradicts")
    ann_mgr.add_annotation_relationship("ann_2", "Gene_1", relation_type="ABOUT")
    ann_mgr.add_annotation_relationship("ann_2", "Disease_1", relation_type="CONTRADICTS")

    # Escalation policy with zero budget to force fallback
    policy = AIEscalationPolicy(
        traversal_mode="hybrid",
        ai_enabled=True,
        ai_budget=0.0  # Zero budget triggers fallback instantly
    )
    mock_provider = MockAIProvider()
    gateway = AIGateway(policy=policy, provider=mock_provider)
    worker = ToGWorker(kg, ann_mgr, ai_gateway=gateway)

    res = worker.execute_query(
        query="What is the evidence regarding Gene_1?",
        traversal_mode="hybrid",
        enable_domain_packs=False,
    )

    # AI should not be called, fallback message is returned
    assert res["metadata"]["ai_calls"] == 0
    assert "Budget limit exhausted" in res["answer"]
    assert res["metadata"]["actual_cost"] == 0.0
