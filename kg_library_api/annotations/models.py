"""
First-class Annotation data models for KG Library.
"""

from typing import Dict, Any
from enum import Enum
from dataclasses import dataclass, field
import datetime
import uuid


class AnnotationType(str, Enum):
    OPINION = "Opinion"
    EVIDENCE = "Evidence"
    OBSERVATION = "Observation"
    ASSERTION = "Assertion"
    HYPOTHESIS = "Hypothesis"
    CORRECTION = "Correction"


class AnnotationToKGRelationType(str, Enum):
    ABOUT = "ABOUT"
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    PROPOSES = "PROPOSES"
    CORRECTS = "CORRECTS"


class AnnotationToAnnotationRelationType(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    REFERS = "REFERS"
    REFINES = "REFINES"
    DERIVED_FROM = "DERIVED_FROM"
    REFERENCES = "REFERENCES"
    RELATED_TO = "RELATED_TO"


@dataclass
class Annotation:
    """Represents a first-class annotation object in KG Library."""
    id: str
    type: str  # AnnotationType string value
    content: str
    author: str = "system"
    timestamp: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    confidence: float = 1.0
    source: str = ""
    provenance: str = ""
    status: str = "active"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content,
            "author": self.author,
            "timestamp": self.timestamp,
            "confidence": self.confidence,
            "source": self.source,
            "provenance": self.provenance,
            "status": self.status,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Annotation":
        return cls(
            id=data.get("id") or data.get("annotation_id") or str(uuid.uuid4()),
            type=data["type"],
            content=data["content"],
            author=data.get("author", "system"),
            timestamp=data.get("timestamp") or datetime.datetime.utcnow().isoformat(),
            confidence=float(data.get("confidence", 1.0)),
            source=data.get("source", ""),
            provenance=data.get("provenance", ""),
            status=data.get("status", "active"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AnnotationRelationship:
    """Represents a relationship originating from an Annotation (to a KG Node or another Annotation)."""
    id: str
    source_annotation_id: str
    target_id: str  # Can be a KG Node ID or an Annotation ID
    target_kind: str  # "KG_NODE" or "ANNOTATION"
    relation_type: str  # AnnotationToKGRelationType or AnnotationToAnnotationRelationType
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_annotation_id": self.source_annotation_id,
            "target_id": self.target_id,
            "target_kind": self.target_kind,
            "relation_type": self.relation_type,
            "properties": self.properties,
        }
