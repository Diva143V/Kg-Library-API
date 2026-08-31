"""
ToGSynthesizer orchestrating three-perspective reasoning and AI Gateway calls.
"""

from typing import Dict, Any, Tuple
from kg_library_api.retrieval.retriever import MultiPerspectiveSearchResult
from kg_library_api.ai.gateway import AIGateway
from kg_library_api.ai.schemas import AIReasonRequest


class ToGSynthesizer:
    """
    Handles response composition and constructs structured summaries for 3 distinct perspectives:
    Knowledge, Expert, and Combined.
    """

    def __init__(self, ai_gateway: AIGateway):
        self.ai_gateway = ai_gateway

    def synthesize(
        self,
        query: str,
        search_res: MultiPerspectiveSearchResult,
        escalate: bool,
        context_str: str
    ) -> Tuple[str, Dict[str, Any], int, float, str, int, float]:
        """
        Synthesizes query responses, building the three perspectives and executing AI calls if escalated.
        Returns:
            Tuple: (answer, perspectives, ai_calls, cost, model_used, tokens_used, budget_remaining)
        """
        # 1. Base perspectives calculation
        knowledge_summary = "Base KG: " + (
            "Paths found linking target entities." if search_res.knowledge_paths
            else "No direct paths found linking target entities."
        )
        expert_summary = "Expert Layer: " + (
            f"Found {len(search_res.annotations)} annotations." if search_res.annotations
            else "No expert annotations recorded."
        )
        combined_summary = "Combined evaluation: "

        if search_res.knowledge_paths and search_res.annotations:
            combined_summary += "Knowledge graph paths align with expert assertions."
        elif search_res.annotations:
            combined_summary += "Expert assertions provide sole evidence; no base KG path exists."
        else:
            combined_summary += "No annotations or base paths to evaluate."

        perspectives = {
            "knowledge": {"summary": knowledge_summary, "paths_count": len(search_res.knowledge_paths)},
            "expert": {"summary": expert_summary, "annotations_count": len(search_res.annotations)},
            "combined": {"summary": combined_summary}
        }

        ai_calls = 0
        cost = 0.0
        model_used = "none"
        tokens_used = 0

        # Execute reasoning
        if escalate and self.ai_gateway.policy.ai_enabled:
            system_prompt = (
                "You are KG Library, a hybrid graph reasoning agent. Format your response clearly "
                "detailing the three distinct perspectives: Knowledge (Base KG), Expert (Annotations), "
                "and Combined (Synthesis of both over current evidence)."
            )
            prompt = f"Query: {query}\n\nContext:\n{context_str}\n\nFormulate your final response."

            ai_req = AIReasonRequest(prompt=prompt, system_prompt=system_prompt)
            ai_res = self.ai_gateway.reason(ai_req)

            if ai_res.model == "fallback":
                ai_calls = 0
                cost = 0.0
                model_used = "fallback"
                tokens_used = 0
                
                parts = []
                if search_res.knowledge_paths:
                    kp_str = " | ".join(p.get("formatted", "") for p in search_res.knowledge_paths)
                    parts.append(f"Identified Knowledge Paths: {kp_str}")
                if search_res.evidence:
                    ev_str = " ; ".join(
                        f"{ev.get('annotation_id') or ev.get('source_pack') or 'Evidence'}: '{ev['content']}'"
                        for ev in search_res.evidence
                    )
                    parts.append(f"Supporting Evidence: {ev_str}")
                if search_res.annotations:
                    ann_str = " ; ".join(f"{a['id']} ({a['type']}): '{a['content']}'" for a in search_res.annotations)
                    parts.append(f"Annotations: {ann_str}")

                if not parts:
                    answer = "Budget limit exhausted for query session. No relevant graph paths or annotations found to answer the query."
                else:
                    answer = "Budget limit exhausted for query session. Based on knowledge graph traversal:\n" + "\n".join(f"- {p}" for p in parts)
                
                perspectives["combined"]["details"] = "Budget limit exhausted for query session."
            else:
                ai_calls = 1
                cost = ai_res.estimated_cost
                model_used = ai_res.model
                tokens_used = ai_res.tokens_used
                answer = ai_res.text
                perspectives["combined"]["details"] = ai_res.text
        else:
            # Deterministic Fallback Synthesis
            parts = []
            if search_res.knowledge_paths:
                kp_str = " | ".join(p.get("formatted", "") for p in search_res.knowledge_paths)
                parts.append(f"Identified Knowledge Paths: {kp_str}")

            if search_res.evidence:
                ev_str = " ; ".join(
                    f"{ev.get('annotation_id') or ev.get('source_pack') or 'Evidence'}: '{ev['content']}'"
                    for ev in search_res.evidence
                )
                parts.append(f"Supporting Evidence: {ev_str}")

            if search_res.annotations:
                ann_str = " ; ".join(f"{a['id']} ({a['type']}): '{a['content']}'" for a in search_res.annotations)
                parts.append(f"Annotations: {ann_str}")

            if not parts:
                answer = "No relevant graph paths or annotations found to answer the query."
            else:
                answer = "Based on knowledge graph traversal:\n" + "\n".join(f"- {p}" for p in parts)

        remaining_budget = max(0.0, self.ai_gateway.policy.ai_budget - self.ai_gateway.total_cost)

        return answer, perspectives, ai_calls, cost, model_used, tokens_used, remaining_budget
