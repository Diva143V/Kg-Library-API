"""
ToG Planner for entity resolution and traversal path planning.
"""

from typing import List
from kg_library_api.core.kg import KnowledgeGraph

_MAX_ENTITY_SCAN = 500  # Safety cap to prevent unbounded full-graph scans


class ToGPlanner:
    """
    Analyzes query and maps text to concrete starting entities.
    Domain-agnostic: matches any node by ID or 'name' property.
    """

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg

    def plan_entities(self, query: str, limit: int = 50) -> List[str]:
        """
        Resolves target entity IDs present in query string using base KG exact/substring mapping.
        Scans at most `_MAX_ENTITY_SCAN` nodes to keep latency bounded on large graphs.
        """
        matched = []
        q_lower = query.lower()
        all_nodes = self.kg.storage.list_nodes(skip=0, limit=_MAX_ENTITY_SCAN)
        for node in all_nodes:
            if len(matched) >= limit:
                break
            nid = node.id.lower()
            name = str(node.properties.get("name", "")).lower()
            if nid in q_lower or (name and name in q_lower):
                matched.append(node.id)
        return matched
