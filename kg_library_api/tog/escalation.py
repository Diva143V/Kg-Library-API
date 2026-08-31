"""
AI Escalation Gate implementation to control reasoning escalation.
"""

from kg_library_api.ai.policy import AIEscalationPolicy
from kg_library_api.retrieval.retriever import MultiPerspectiveSearchResult


class EscalationGate:
    """
    Checks policy conditions and queries to determine whether to escalate to LLMs.
    """

    def __init__(self, policy: AIEscalationPolicy):
        self.policy = policy

    def should_escalate(self, query: str, search_res: MultiPerspectiveSearchResult) -> bool:
        """Evaluate query and search results to decide if AI reasoning is required."""
        if not self.policy.ai_enabled:
            return False
        if self.policy.traversal_mode == "ai":
            return True
        if self.policy.traversal_mode == "manual":
            return False

        # Hybrid triggers:
        # 1. Contradictory evidence (both SUPPORTS and CONTRADICTS in annotation paths)
        rel_types = [ap.get("relation_type") for ap in search_res.annotation_paths]
        if "SUPPORTS" in rel_types and "CONTRADICTS" in rel_types:
            return True

        # 2. Expert annotations exist but no base KG path exists to explain them
        if not search_res.knowledge_paths and search_res.annotations:
            return True

        # 3. Multiple external sources require semantic synthesis
        if len(search_res.evidence) > 1 or len(search_res.annotations) > 1:
            return True

        return False
