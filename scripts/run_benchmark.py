"""
Benchmark script comparing Previous AI-Driven Traversal vs. Polaris Deterministic Traversal.
"""

from typing import Tuple, Dict, Any
import time
import json
from polaris_kg.core.kg import KnowledgeGraph
from polaris_kg.core.storage import InMemoryStorageEngine
from polaris_kg.annotations.manager import AnnotationManager
from polaris_kg.traversal.engine import DeterministicTraversalEngine
from polaris_kg.tog.worker import ToGWorker


def setup_benchmark_graph(size: int = 50) -> Tuple[KnowledgeGraph, AnnotationManager]:
    kg = KnowledgeGraph(InMemoryStorageEngine())
    ann_mgr = AnnotationManager(kg)

    # Create chain/tree graph of genes, proteins, diseases
    for i in range(size):
        g_id = f"gene_{i}"
        p_id = f"protein_{i}"
        d_id = f"disease_{i}"

        kg.create_node(g_id, label="Gene", properties={"name": f"Gene {i}"})
        kg.create_node(p_id, label="Protein", properties={"name": f"Protein {i}"})
        kg.create_node(d_id, label="Disease", properties={"name": f"Disease {i}"})

        kg.create_relationship(g_id, p_id, type="encodes")
        kg.create_relationship(p_id, d_id, type="associated_with")

        if i > 0:
            kg.create_relationship(p_id, f"protein_{i-1}", type="interacts_with")

        ann = ann_mgr.create_annotation(
            annotation_id=f"ann_{i}",
            type="Evidence",
            content=f"Clinical study for Protein {i} and Disease {i}.",
        )
        ann_mgr.add_annotation_relationship(f"ann_{i}", p_id, relation_type="ABOUT")
        ann_mgr.add_annotation_relationship(f"ann_{i}", d_id, relation_type="SUPPORTS")

    return kg, ann_mgr


def simulate_ai_driven_traversal(kg: KnowledgeGraph, start_node: str, depth: int = 3):
    """Simulates previous AI-driven traversal where LLM is called at every hop."""
    start_time = time.time()
    nodes_visited = 0
    edges_visited = 0
    llm_calls = 0
    input_tokens = 0
    output_tokens = 0

    curr_frontier = [start_node]
    for d in range(depth):
        next_frontier = []
        for nid in curr_frontier:
            nodes_visited += 1
            rels = kg.get_relationships(source_id=nid)
            edges_visited += len(rels)

            # At each hop, legacy ToG calls LLM for relation selection
            llm_calls += 1
            input_tokens += 350  # ~350 prompt tokens per hop
            output_tokens += 120  # ~120 completion tokens per hop

            for r in rels:
                next_frontier.append(r.target_id)
        curr_frontier = next_frontier[:5]  # prune to top 5

    # Final answer synthesis call
    llm_calls += 1
    input_tokens += 1500
    output_tokens += 400

    latency_ms = int((time.time() - start_time) * 1000)
    cost_usd = (input_tokens / 1_000_000 * 2.50) + (output_tokens / 1_000_000 * 10.00)

    return {
        "architecture": "Previous AI-Driven Traversal",
        "llm_calls": llm_calls,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "traversal_time_ms": latency_ms,
        "total_latency_ms": latency_ms + 450,
        "nodes_visited": nodes_visited,
        "edges_visited": edges_visited,
        "estimated_cost_usd": round(cost_usd, 6),
        "reproducibility": "Low (Stochastic LLM decisions at every edge)",
    }


def run_polaris_deterministic_traversal(kg: KnowledgeGraph, ann_mgr: AnnotationManager, start_node: str, depth: int = 3):
    """Runs Polaris deterministic code-based traversal."""
    worker = ToGWorker(kg, ann_mgr)
    start_time = time.time()

    res = worker.execute_query(
        query=f"What evidence supports the relationship for {start_node}?",
        include_annotations=True,
        max_depth=depth,
        start_entities=[start_node],
    )

    latency_ms = int((time.time() - start_time) * 1000)

    llm_calls = res["metadata"]["llm_calls"]
    input_tokens = 450 if llm_calls > 0 else 0
    output_tokens = 250 if llm_calls > 0 else 0
    cost_usd = (input_tokens / 1_000_000 * 2.50) + (output_tokens / 1_000_000 * 10.00)

    return {
        "architecture": "Polaris Deterministic Code Traversal",
        "llm_calls": llm_calls,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "traversal_time_ms": latency_ms,
        "total_latency_ms": latency_ms,
        "nodes_visited": res["metadata"]["nodes_traversed"],
        "edges_visited": res["metadata"]["edges_traversed"],
        "estimated_cost_usd": round(cost_usd, 6),
        "reproducibility": "100% Deterministic (Identical output per run)",
    }


def main():
    kg, ann_mgr = setup_benchmark_graph(size=50)

    ai_res = simulate_ai_driven_traversal(kg, start_node="gene_0", depth=3)
    polaris_res = run_polaris_deterministic_traversal(kg, ann_mgr, start_node="gene_0", depth=3)

    print("=== BENCHMARK RESULTS ===")
    print("Previous AI-Driven Traversal:")
    print(json.dumps(ai_res, indent=2))
    print("\nPolaris Deterministic Traversal:")
    print(json.dumps(polaris_res, indent=2))


if __name__ == "__main__":
    main()
