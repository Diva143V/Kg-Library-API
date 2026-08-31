"""
Database manager for expert annotation persistence.
"""

from typing import List, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from kg_library_api.core.schema import (
    Base,
    SQLAnnotation,
    SQLAnnotationRelationship,
    SQLAnnotationCollection,
)
from kg_library_api.annotations.models import (
    Annotation,
    AnnotationRelationship,
)
from kg_library_api.core.models import Collection


class SQLAnnotationStorage:
    """Manages CRUD operations for expert annotations in SQL."""

    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def create_annotation(self, ann: Annotation) -> Annotation:
        with self.Session() as session:
            sql_ann = SQLAnnotation(
                id=ann.id,
                type=ann.type.value if hasattr(ann.type, "value") else ann.type,
                content=ann.content,
                author=ann.author,
                timestamp=ann.timestamp,
                confidence=ann.confidence,
                source=ann.source,
                provenance=ann.provenance,
                status=ann.status,
                metadata_fields=ann.metadata
            )
            session.merge(sql_ann)
            session.commit()
            return ann

    def get_annotation(self, ann_id: str) -> Optional[Annotation]:
        with self.Session() as session:
            r = session.query(SQLAnnotation).filter(SQLAnnotation.id == ann_id).first()
            if not r:
                return None
            return Annotation(
                id=r.id,
                type=r.type,
                content=r.content,
                author=r.author,
                timestamp=r.timestamp,
                confidence=r.confidence,
                source=r.source,
                provenance=r.provenance,
                status=r.status,
                metadata=r.metadata_fields or {}
            )

    def delete_annotation(self, ann_id: str) -> bool:
        with self.Session() as session:
            r = session.query(SQLAnnotation).filter(SQLAnnotation.id == ann_id).first()
            if not r:
                return False
            session.query(SQLAnnotationRelationship).filter(
                (SQLAnnotationRelationship.source_annotation_id == ann_id) | 
                ((SQLAnnotationRelationship.target_id == ann_id) & (SQLAnnotationRelationship.target_kind == "ANNOTATION"))
            ).delete()
            session.delete(r)
            session.commit()
            return True

    def create_annotation_relationship(self, rel: AnnotationRelationship) -> AnnotationRelationship:
        with self.Session() as session:
            sql_rel = SQLAnnotationRelationship(
                id=rel.id,
                source_annotation_id=rel.source_annotation_id,
                target_id=rel.target_id,
                target_kind=rel.target_kind,
                relation_type=rel.relation_type,
                properties=rel.properties
            )
            session.merge(sql_rel)
            session.commit()
            return rel

    def get_annotation_relationships(
        self,
        source_annotation_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relation_type: Optional[str] = None,
    ) -> List[AnnotationRelationship]:
        with self.Session() as session:
            q = session.query(SQLAnnotationRelationship)
            if source_annotation_id:
                q = q.filter(SQLAnnotationRelationship.source_annotation_id == source_annotation_id)
            if target_id:
                q = q.filter(SQLAnnotationRelationship.target_id == target_id)
            if relation_type:
                q = q.filter(SQLAnnotationRelationship.relation_type == relation_type)
            
            rels = q.all()
            return [
                AnnotationRelationship(
                    id=r.id,
                    source_annotation_id=r.source_annotation_id,
                    target_id=r.target_id,
                    target_kind=r.target_kind,
                    relation_type=r.relation_type,
                    properties=r.properties or {}
                )
                for r in rels
            ]

    def create_collection(self, collection: Collection) -> Collection:
        with self.Session() as session:
            sql_coll = SQLAnnotationCollection(
                id=collection.id,
                name=collection.name,
                description=collection.description,
                annotation_ids=collection.node_ids
            )
            session.merge(sql_coll)
            session.commit()
            return collection

    def get_collection(self, collection_id: str) -> Optional[Collection]:
        with self.Session() as session:
            c = session.query(SQLAnnotationCollection).filter(SQLAnnotationCollection.id == collection_id).first()
            if not c:
                return None
            return Collection(
                id=c.id,
                name=c.name,
                description=c.description or "",
                node_ids=c.annotation_ids or [],  # maps collection node_ids to annotation_ids
                relationship_ids=[]
            )

    def add_to_collection(self, collection_id: str, annotation_ids: List[str]) -> bool:
        with self.Session() as session:
            c = session.query(SQLAnnotationCollection).filter(SQLAnnotationCollection.id == collection_id).first()
            if not c:
                return False
            curr = list(c.annotation_ids or [])
            for aid in annotation_ids:
                if aid not in curr:
                    curr.append(aid)
            c.annotation_ids = curr
            session.commit()
            return True
