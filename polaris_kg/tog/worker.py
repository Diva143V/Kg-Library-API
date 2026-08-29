"""
Think-on-Graph (ToG) Worker Implementation for Polaris.
"""

from typing import Dict, Any, List, Optional, Tuple
import time
import re
from polaris_kg.core.kg import KnowledgeGraph
from polaris_kg.annotations.manager import AnnotationManager
from polaris_kg.retrieval.retriever import AnnotationAwareRetriever, RetrievalMode, MultiPerspectiveSearchResult
from polaris_kg.ai.gateway import AIGateway
from polaris_kg.tog.planner import ToGPlanner
from polaris_kg.tog.escalation import EscalationGate
from polaris_kg.tog.context_builder import ContextBuilder
from polaris_kg.tog.synthesizer import ToGSynthesizer


class ToGWorker:
    """
    Think-on-Graph (ToG) Worker.
    Uses deterministic program-code graph traversal to retrieve subgraphs and evidence,
    and delegating query understanding & final answer synthesis to LLMs (or fallback synthesis engine).
    """

    def __init__(
        self,
        base_kg: KnowledgeGraph,
        annotation_mgr: AnnotationManager,
        llm: Optional[Any] = None,
        ai_gateway: Optional[AIGateway] = None
    ):
        self.base_kg = base_kg
        self.annotation_mgr = annotation_mgr
        self.retriever = AnnotationAwareRetriever(base_kg, annotation_mgr)
        self.llm = llm

        # Initialize AI components
        self.ai_gateway = ai_gateway or AIGateway()
        self.planner = ToGPlanner(base_kg)
        self.escalation_gate = EscalationGate(self.ai_gateway.policy)
        self.synthesizer = ToGSynthesizer(self.ai_gateway)

    def execute_query(
        self,
        query: str,
        include_annotations: bool = True,
        max_depth: int = 3,
        start_entities: Optional[List[str]] = None,
        traversal_mode: str = "manual",  # "manual", "ai", or "hybrid"
        enable_domain_packs: bool = True,
        ai_enabled: Optional[bool] = None,
        max_ai_calls: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Executes query, using deterministic code-driven traversal first,
        and optionally escalating to AI gateway for semantic reasoning.
        """
        start_time = time.time()

        # Temporary policy overrides
        if ai_enabled is not None:
            self.ai_gateway.policy.ai_enabled = ai_enabled
        if max_ai_calls is not None:
            self.ai_gateway.policy.max_ai_calls = max_ai_calls
        if traversal_mode in ("manual", "ai", "hybrid"):
            self.ai_gateway.policy.traversal_mode = traversal_mode

        # Step 1: Entity Identification via planner
        target_entities = start_entities or []
        if not target_entities:
            target_entities = self.planner.plan_entities(query)

        # Step 2: Deterministic Traversal & Retrieval (with latency timing)
        python_start = time.time()
        mode = RetrievalMode.HYBRID_BASE_AND_ANNOTATION if include_annotations else RetrievalMode.BASE_KG_ONLY
        search_res: MultiPerspectiveSearchResult = self.retriever.retrieve(
            start_entity_ids=target_entities,
            mode=mode,
            max_depth=max_depth,
            traversal_mode=traversal_mode if traversal_mode != "hybrid" else "manual",
            llm=self.llm,
            query=query,
            enable_domain_packs=enable_domain_packs,
        )
        python_traversal_ms = int((time.time() - python_start) * 1000)

        # Count traversed metrics
        nodes_traversed = set(target_entities)
        edges_traversed = set()
        for kp in search_res.knowledge_paths:
            for n in kp.get("nodes", []):
                nodes_traversed.add(n["id"])
            for r in kp.get("relationships", []):
                edges_traversed.add(r["id"])

        # Step 3: Context Construction
        context_str = ContextBuilder.build_prompt_context(search_res)

        # Step 4: Escalation Check
        escalate = self.escalation_gate.should_escalate(query, search_res)
        escalation_reason = "none"
        if escalate:
            # Determine primary reason
            rel_types = [ap.get("relation_type") for ap in search_res.annotation_paths]
            if "SUPPORTS" in rel_types and "CONTRADICTS" in rel_types:
                escalation_reason = "conflicting_evidence"
            elif not search_res.knowledge_paths and search_res.annotations:
                escalation_reason = "explain_annotations"
            else:
                escalation_reason = "complex_synthesis"

        # 5. Pre-escalation Estimations for Observability
        active_provider = self.ai_gateway.custom_provider or self.ai_gateway.local_provider
        prompt_tokens = active_provider.count_tokens(context_str)
        estimated_tokens = prompt_tokens + 500  # assuming 500 output tokens
        estimated_cost = active_provider.estimate_cost(prompt_tokens, 500)

        # Step 5: Synthesis
        answer, perspectives, ai_calls, cost, model_used, actual_tokens, budget_remaining = self.synthesizer.synthesize(
            query=query,
            search_res=search_res,
            escalate=escalate,
            context_str=context_str
        )

        latency_ms = int((time.time() - start_time) * 1000)

        return {
            "answer": answer,
            "knowledge_paths": search_res.knowledge_paths,
            "annotation_paths": search_res.annotation_paths,
            "annotations": search_res.annotations,
            "perspectives": perspectives,
            "evidence": search_res.evidence,
            "provenance": search_res.provenance,
            "metadata": {
                "traversal_mode": self.ai_gateway.policy.traversal_mode,
                "python_traversal_ms": python_traversal_ms,
                "ai_calls": ai_calls,
                "ai_provider": model_used.split("-")[0] if model_used != "none" else "none",
                "ai_model": model_used,
                "estimated_tokens": estimated_tokens if escalate else 0,
                "actual_tokens": actual_tokens,
                "estimated_cost": estimated_cost if escalate else 0.0,
                "actual_cost": cost,
                "cache_hit": False,
                "escalation_reason": escalation_reason,
                "budget_remaining": budget_remaining,
                "nodes_traversed": len(nodes_traversed),
                "edges_traversed": len(edges_traversed),
                "latency_ms": latency_ms,
            },
        }
