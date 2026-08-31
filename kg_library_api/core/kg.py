"""
Knowledge Graph core implementation for KG Library.
"""

from typing import Dict, Any, List, Optional
import uuid
from kg_library_api.core.models import Node, Relationship, Collection, Subgraph
from kg_library_api.core.storage import BaseStorageEngine, InMemoryStorageEngine


class KnowledgeGraph:
    """
    Reusable Knowledge Graph facade. Decouples graph operations from the underlying storage engine.
    """

    def __init__(self, storage_engine: Optional[BaseStorageEngine] = None):
        self.storage: BaseStorageEngine = storage_engine or InMemoryStorageEngine()

    def create_node(
        self,
        node_id: Optional[str] = None,
        label: str = "Node",
        properties: Optional[Dict[str, Any]] = None,
    ) -> Node:
        nid = node_id or str(uuid.uuid4())
        props = properties or {}
        node = Node(id=nid, label=label, properties=props)
        return self.storage.create_node(node)

    def get_node(self, node_id: str) -> Optional[Node]:
        return self.storage.get_node(node_id)

    def update_node(
        self,
        node_id: str,
        properties: Dict[str, Any],
        label: Optional[str] = None,
    ) -> Optional[Node]:
        return self.storage.update_node(node_id, properties, label)

    def delete_node(self, node_id: str) -> bool:
        return self.storage.delete_node(node_id)

    def create_relationship(
        self,
        source_id: str,
        target_id: str,
        type: str,
        rel_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        directed: bool = True,
    ) -> Relationship:
        rid = rel_id or str(uuid.uuid4())
        props = properties or {}
        rel = Relationship(
            id=rid,
            source_id=source_id,
            target_id=target_id,
            type=type,
            properties=props,
            directed=directed,
        )
        return self.storage.create_relationship(rel)

    def get_relationships(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relationship_type: Optional[str] = None,
    ) -> List[Relationship]:
        return self.storage.get_relationships(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
        )

    def create_collection(
        self,
        name: str,
        collection_id: Optional[str] = None,
        description: str = "",
        node_ids: Optional[List[str]] = None,
        relationship_ids: Optional[List[str]] = None,
    ) -> Collection:
        cid = collection_id or str(uuid.uuid4())
        nids = node_ids or []
        rids = relationship_ids or []
        coll = Collection(
            id=cid,
            name=name,
            description=description,
            node_ids=nids,
            relationship_ids=rids,
        )
        return self.storage.create_collection(coll)

    def get_collection(self, collection_id: str) -> Optional[Collection]:
        return self.storage.get_collection(collection_id)

    def add_to_collection(
        self,
        collection_id: str,
        node_ids: Optional[List[str]] = None,
        relationship_ids: Optional[List[str]] = None,
    ) -> bool:
        return self.storage.add_to_collection(
            collection_id=collection_id,
            node_ids=node_ids or [],
            relationship_ids=relationship_ids or [],
        )

    def query(self, filters: Dict[str, Any]) -> List[Node]:
        return self.storage.query(filters)

    def get_subgraph(self, node_ids: List[str], depth: int = 1) -> Subgraph:
        return self.storage.get_subgraph(node_ids, depth)
