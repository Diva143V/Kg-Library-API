"""
ToG Planner for entity resolution and traversal path planning.
"""

from typing import List
from polaris_kg.core.kg import KnowledgeGraph


class ToGPlanner:
    """
    Analyzes query and maps text to concrete starting entities.
    """

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg

    def plan_entities(self, query: str) -> List[str]:
        """Resolves target entity IDs present in query string using base KG exact/substring mapping."""
        matched = []
        q_lower = query.lower()
        all_nodes = self.kg.query({})
        for node in all_nodes:
            nid = node.id.lower()
            name = str(node.properties.get("name", "")).lower()
            if nid in q_lower or (name and name in q_lower):
                matched.append(node.id)
        return matched
