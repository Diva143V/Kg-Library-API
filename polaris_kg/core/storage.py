"""
Storage abstraction and in-memory implementation for Polaris Knowledge Graph.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from polaris_kg.core.models import Node, Relationship, Collection, Subgraph


class BaseStorageEngine(ABC):
    """Abstract base storage engine interface."""

    @abstractmethod
    def create_node(self, node: Node) -> Node:
        pass

    @abstractmethod
    def get_node(self, node_id: str) -> Optional[Node]:
        pass

    @abstractmethod
    def update_node(self, node_id: str, properties: Dict[str, Any], label: Optional[str] = None) -> Optional[Node]:
        pass

    @abstractmethod
    def delete_node(self, node_id: str) -> bool:
        pass

    @abstractmethod
    def create_relationship(self, relationship: Relationship) -> Relationship:
        pass

    @abstractmethod
    def get_relationships(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relationship_type: Optional[str] = None,
    ) -> List[Relationship]:
        pass

    @abstractmethod
    def create_collection(self, collection: Collection) -> Collection:
        pass

    @abstractmethod
    def get_collection(self, collection_id: str) -> Optional[Collection]:
        pass

    @abstractmethod
    def add_to_collection(self, collection_id: str, node_ids: List[str], relationship_ids: List[str]) -> bool:
        pass

    @abstractmethod
    def query(self, filters: Dict[str, Any]) -> List[Node]:
        pass

    @abstractmethod
    def get_subgraph(self, node_ids: List[str], depth: int = 1) -> Subgraph:
        pass


class InMemoryStorageEngine(BaseStorageEngine):
    """In-memory storage engine implementation."""

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.relationships: Dict[str, Relationship] = {}
        self.collections: Dict[str, Collection] = {}

    def create_node(self, node: Node) -> Node:
        self.nodes[node.id] = node
        return node

    def get_node(self, node_id: str) -> Optional[Node]:
        return self.nodes.get(node_id)

    def update_node(self, node_id: str, properties: Dict[str, Any], label: Optional[str] = None) -> Optional[Node]:
        node = self.nodes.get(node_id)
        if not node:
            return None
        if label:
            node.label = label
        node.properties.update(properties)
        return node

    def delete_node(self, node_id: str) -> bool:
        if node_id not in self.nodes:
            return False
        del self.nodes[node_id]
        # Remove associated relationships
        rel_ids_to_del = [
            r_id for r_id, r in self.relationships.items()
            if r.source_id == node_id or r.target_id == node_id
        ]
        for r_id in rel_ids_to_del:
            del self.relationships[r_id]
        return True

    def create_relationship(self, relationship: Relationship) -> Relationship:
        self.relationships[relationship.id] = relationship
        return relationship

    def get_relationships(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relationship_type: Optional[str] = None,
    ) -> List[Relationship]:
        results = []
        for rel in self.relationships.values():
            if source_id and rel.source_id != source_id:
                continue
            if target_id and rel.target_id != target_id:
                continue
            if relationship_type and rel.type != relationship_type:
                continue
            results.append(rel)
        return results

    def create_collection(self, collection: Collection) -> Collection:
        self.collections[collection.id] = collection
        return collection

    def get_collection(self, collection_id: str) -> Optional[Collection]:
        return self.collections.get(collection_id)

    def add_to_collection(self, collection_id: str, node_ids: List[str], relationship_ids: List[str]) -> bool:
        coll = self.collections.get(collection_id)
        if not coll:
            return False
        for nid in node_ids:
            if nid not in coll.node_ids:
                coll.node_ids.append(nid)
        for rid in relationship_ids:
            if rid not in coll.relationship_ids:
                coll.relationship_ids.append(rid)
        return True

    def query(self, filters: Dict[str, Any]) -> List[Node]:
        """Query nodes matching label and/or property key-value pairs."""
        matching = []
        target_label = filters.get("label")
        target_props = filters.get("properties", {})
        query_text = filters.get("query", "").lower()

        for node in self.nodes.values():
            if target_label and node.label != target_label:
                continue
            match_props = True
            for k, v in target_props.items():
                if node.properties.get(k) != v:
                    match_props = False
                    break
            if not match_props:
                continue

            if query_text:
                # Search node ID, label, or property values
                text_content = f"{node.id} {node.label} {' '.join(str(v) for v in node.properties.values())}".lower()
                if query_text not in text_content:
                    continue

            matching.append(node)
        return matching

    def get_subgraph(self, node_ids: List[str], depth: int = 1) -> Subgraph:
        visited_nodes = set()
        frontier = set(node_ids)
        collected_relationships = set()

        for _ in range(depth + 1):
            next_frontier = set()
            for nid in frontier:
                if nid in visited_nodes or nid not in self.nodes:
                    continue
                visited_nodes.add(nid)

                for rel in self.relationships.values():
                    if rel.source_id == nid:
                        collected_relationships.add(rel.id)
                        next_frontier.add(rel.target_id)
                    elif rel.target_id == nid:
                        collected_relationships.add(rel.id)
                        next_frontier.add(rel.source_id)
            frontier = next_frontier

        nodes = [self.nodes[nid] for nid in visited_nodes if nid in self.nodes]
        relationships = [self.relationships[rid] for rid in collected_relationships if rid in self.relationships]
        return Subgraph(nodes=nodes, relationships=relationships)


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from polaris_kg.core.schema import Base, SQLNode, SQLRelationship, SQLCollection


class SQLStorageEngine(BaseStorageEngine):
    """SQL Database Storage Engine (PostgreSQL/Supabase or SQLite) using SQLAlchemy."""

    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def create_node(self, node: Node) -> Node:
        with self.Session() as session:
            sql_node = SQLNode(id=node.id, label=node.label, properties=node.properties)
            session.merge(sql_node)
            session.commit()
            return node

    def get_node(self, node_id: str) -> Optional[Node]:
        with self.Session() as session:
            sql_node = session.query(SQLNode).filter(SQLNode.id == node_id).first()
            if not sql_node:
                return None
            return Node(id=sql_node.id, label=sql_node.label, properties=sql_node.properties or {})

    def update_node(self, node_id: str, properties: Dict[str, Any], label: Optional[str] = None) -> Optional[Node]:
        with self.Session() as session:
            sql_node = session.query(SQLNode).filter(SQLNode.id == node_id).first()
            if not sql_node:
                return None
            if label:
                sql_node.label = label
            current_props = dict(sql_node.properties or {})
            current_props.update(properties)
            sql_node.properties = current_props
            session.commit()
            return Node(id=sql_node.id, label=sql_node.label, properties=sql_node.properties)

    def delete_node(self, node_id: str) -> bool:
        with self.Session() as session:
            sql_node = session.query(SQLNode).filter(SQLNode.id == node_id).first()
            if not sql_node:
                return False
            session.query(SQLRelationship).filter(
                (SQLRelationship.source_id == node_id) | (SQLRelationship.target_id == node_id)
            ).delete()
            session.delete(sql_node)
            session.commit()
            return True

    def create_relationship(self, relationship: Relationship) -> Relationship:
        with self.Session() as session:
            sql_rel = SQLRelationship(
                id=relationship.id,
                source_id=relationship.source_id,
                target_id=relationship.target_id,
                type=relationship.type,
                properties=relationship.properties,
                directed=relationship.directed
            )
            session.merge(sql_rel)
            session.commit()
            return relationship

    def get_relationships(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relationship_type: Optional[str] = None,
    ) -> List[Relationship]:
        with self.Session() as session:
            q = session.query(SQLRelationship)
            if source_id:
                q = q.filter(SQLRelationship.source_id == source_id)
            if target_id:
                q = q.filter(SQLRelationship.target_id == target_id)
            if relationship_type:
                q = q.filter(SQLRelationship.type == relationship_type)
            rels = q.all()
            return [
                Relationship(
                    id=r.id,
                    source_id=r.source_id,
                    target_id=r.target_id,
                    type=r.type,
                    properties=r.properties or {},
                    directed=r.directed
                )
                for r in rels
            ]

    def create_collection(self, collection: Collection) -> Collection:
        with self.Session() as session:
            sql_coll = SQLCollection(
                id=collection.id,
                name=collection.name,
                description=collection.description,
                node_ids=collection.node_ids,
                relationship_ids=collection.relationship_ids
            )
            session.merge(sql_coll)
            session.commit()
            return collection

    def get_collection(self, collection_id: str) -> Optional[Collection]:
        with self.Session() as session:
            c = session.query(SQLCollection).filter(SQLCollection.id == collection_id).first()
            if not c:
                return None
            return Collection(
                id=c.id,
                name=c.name,
                description=c.description or "",
                node_ids=c.node_ids or [],
                relationship_ids=c.relationship_ids or []
            )

    def add_to_collection(self, collection_id: str, node_ids: List[str], relationship_ids: List[str]) -> bool:
        with self.Session() as session:
            c = session.query(SQLCollection).filter(SQLCollection.id == collection_id).first()
            if not c:
                return False
            curr_nodes = list(c.node_ids or [])
            for nid in node_ids:
                if nid not in curr_nodes:
                    curr_nodes.append(nid)
            c.node_ids = curr_nodes

            curr_rels = list(c.relationship_ids or [])
            for rid in relationship_ids:
                if rid not in curr_rels:
                    curr_rels.append(rid)
            c.relationship_ids = curr_rels
            
            session.commit()
            return True

    def query(self, filters: Dict[str, Any]) -> List[Node]:
        with self.Session() as session:
            q = session.query(SQLNode)
            target_label = filters.get("label")
            target_props = filters.get("properties", {})
            query_text = filters.get("query", "").lower()

            if target_label:
                q = q.filter(SQLNode.label == target_label)
            
            nodes = q.all()
            matching = []
            for node in nodes:
                props = node.properties or {}
                match_props = True
                for k, v in target_props.items():
                    if props.get(k) != v:
                        match_props = False
                        break
                if not match_props:
                    continue

                if query_text:
                    text_content = f"{node.id} {node.label} {' '.join(str(v) for v in props.values())}".lower()
                    if query_text not in text_content:
                        continue

                matching.append(
                    Node(id=node.id, label=node.label, properties=props)
                )
            return matching

    def get_subgraph(self, node_ids: List[str], depth: int = 1) -> Subgraph:
        with self.Session() as session:
            visited_nodes = set()
            frontier = set(node_ids)
            collected_relationships = set()

            for _ in range(depth + 1):
                next_frontier = set()
                for nid in frontier:
                    if nid in visited_nodes:
                        continue
                    node_exists = session.query(SQLNode).filter(SQLNode.id == nid).first()
                    if not node_exists:
                        continue
                    visited_nodes.add(nid)

                    rels = session.query(SQLRelationship).filter(
                        (SQLRelationship.source_id == nid) | (SQLRelationship.target_id == nid)
                    ).all()
                    for r in rels:
                        collected_relationships.add(r.id)
                        if r.source_id == nid:
                            next_frontier.add(r.target_id)
                        else:
                            next_frontier.add(r.source_id)
                frontier = next_frontier

            nodes_list = []
            for nid in visited_nodes:
                n = session.query(SQLNode).filter(SQLNode.id == nid).first()
                if n:
                    nodes_list.append(Node(id=n.id, label=n.label, properties=n.properties or {}))

            rels_list = []
            for rid in collected_relationships:
                r = session.query(SQLRelationship).filter(SQLRelationship.id == rid).first()
                if r:
                    rels_list.append(Relationship(
                        id=r.id,
                        source_id=r.source_id,
                        target_id=r.target_id,
                        type=r.type,
                        properties=r.properties or {},
                        directed=r.directed
                    ))

            return Subgraph(nodes=nodes_list, relationships=rels_list)
