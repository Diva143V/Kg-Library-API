"""
Polaris Knowledge Graph Package Interface.

Exposes stable deliverables for Polaris integration:
1. Knowledge-Graph Annotation API & Store
2. Think-on-Graph Worker API & Engine
3. Shared Knowledge Graph Core & Deterministic Traversal
"""

from polaris_kg.core.models import Node, Relationship, Collection, Subgraph
from polaris_kg.core.storage import BaseStorageEngine, InMemoryStorageEngine
from polaris_kg.core.kg import KnowledgeGraph
from polaris_kg.traversal.engine import DeterministicTraversalEngine, TraversalResult, TraversalPath
from polaris_kg.annotations.models import (
    Annotation,
    AnnotationRelationship,
    AnnotationType,
    AnnotationToKGRelationType,
    AnnotationToAnnotationRelationType,
)
from polaris_kg.annotations.manager import AnnotationManager
from polaris_kg.retrieval.retriever import AnnotationAwareRetriever, RetrievalMode, MultiPerspectiveSearchResult
from polaris_kg.retrieval.packs import ToolManager, DomainPackManifest, TinyFishClient
from polaris_kg.ai import AIGateway, AIEscalationPolicy
from polaris_kg.tog.worker import ToGWorker
from polaris_kg.tog.planner import ToGPlanner
from polaris_kg.tog.escalation import EscalationGate
from polaris_kg.tog.context_builder import ContextBuilder
from polaris_kg.tog.synthesizer import ToGSynthesizer
from polaris_kg.api.app import app as polaris_api_app

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
    "polaris_api_app",
]
