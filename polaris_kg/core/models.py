"""
Core data models for Polaris Knowledge Graph.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import uuid


@dataclass
class Node:
    """Represents a node in the Knowledge Graph."""
    id: str
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "properties": self.properties,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node":
        return cls(
            id=data["id"],
            label=data.get("label", "Node"),
            properties=data.get("properties", {}),
        )


@dataclass
class Relationship:
    """Represents a directed relationship/edge in the Knowledge Graph."""
    id: str
    source_id: str
    target_id: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    directed: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.type,
            "properties": self.properties,
            "directed": self.directed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Relationship":
        return cls(
            id=data["id"],
            source_id=data["source_id"],
            target_id=data["target_id"],
            type=data["type"],
            properties=data.get("properties", {}),
            directed=data.get("directed", True),
        )


@dataclass
class Collection:
    """Represents a collection of nodes and relationships."""
    id: str
    name: str
    description: str = ""
    node_ids: List[str] = field(default_factory=list)
    relationship_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "node_ids": self.node_ids,
            "relationship_ids": self.relationship_ids,
        }


@dataclass
class Subgraph:
    """Represents a extracted subgraph containing nodes and relationships."""
    nodes: List[Node] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "relationships": [r.to_dict() for r in self.relationships],
        }
