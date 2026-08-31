"""
KG Library Knowledge Graph Package Interface.

Exposes stable deliverables for KG Library integration:
1. Knowledge-Graph Annotation API & Store
2. Think-on-Graph Worker API & Engine
3. Shared Knowledge Graph Core & Deterministic Traversal
"""

from kg_library_api.core.models import Node, Relationship, Collection, Subgraph
from kg_library_api.core.storage import BaseStorageEngine, InMemoryStorageEngine
from kg_library_api.core.kg import KnowledgeGraph
from kg_library_api.traversal.engine import DeterministicTraversalEngine, TraversalResult, TraversalPath
from kg_library_api.annotations.models import (
    Annotation,
    AnnotationRelationship,
    AnnotationType,
    AnnotationToKGRelationType,
    AnnotationToAnnotationRelationType,
)
from kg_library_api.annotations.manager import AnnotationManager
from kg_library_api.retrieval.retriever import AnnotationAwareRetriever, RetrievalMode, MultiPerspectiveSearchResult
from kg_library_api.retrieval.packs import ToolManager, DomainPackManifest, TinyFishClient
from kg_library_api.ai import AIGateway, AIEscalationPolicy
from kg_library_api.tog.worker import ToGWorker
from kg_library_api.tog.planner import ToGPlanner
from kg_library_api.tog.escalation import EscalationGate
from kg_library_api.tog.context_builder import ContextBuilder
from kg_library_api.tog.synthesizer import ToGSynthesizer
from kg_library_api.api.app import app as kg_library_api_app

__all__ = [
    # Core KG
    "Node",
    "Relationship",
    "Collection",
    "Subgraph",
    "BaseStorageEngine",
    "InMemoryStorageEngine",
    "KnowledgeGraph",
    # Traversal
    "DeterministicTraversalEngine",
    "TraversalResult",
    "TraversalPath",
    # Annotations
    "Annotation",
    "AnnotationRelationship",
    "AnnotationType",
    "AnnotationToKGRelationType",
    "AnnotationToAnnotationRelationType",
    "AnnotationManager",
    # Retrieval
    "AnnotationAwareRetriever",
    "RetrievalMode",
    "MultiPerspectiveSearchResult",
    "ToolManager",
    "DomainPackManifest",
    "TinyFishClient",
    # AI Gateway
    "AIGateway",
    "AIEscalationPolicy",
    # ToG Worker and components
    "ToGWorker",
    "ToGPlanner",
    "EscalationGate",
    "ContextBuilder",
    "ToGSynthesizer",
    # API Application Deliverable
    "kg_library_api_app",
]
