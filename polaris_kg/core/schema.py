"""
SQLAlchemy schemas for Polaris Knowledge Graph and Annotation tables.
"""

from sqlalchemy import Column, String, Boolean, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SQLNode(Base):
    __tablename__ = "nodes"

    id = Column(String, primary_key=True)
    label = Column(String, nullable=False)
    properties = Column(JSON, default=dict)


class SQLRelationship(Base):
    __tablename__ = "relationships"

    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(String, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False)
    properties = Column(JSON, default=dict)
    directed = Column(Boolean, default=True)


class SQLCollection(Base):
    __tablename__ = "collections"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    node_ids = Column(JSON, default=list)
    relationship_ids = Column(JSON, default=list)


class SQLAnnotation(Base):
    __tablename__ = "annotations"

    id = Column(String, primary_key=True)
    type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String, default="system")
    timestamp = Column(String, nullable=False)
    confidence = Column(Float, default=1.0)
    source = Column(String, default="")
    provenance = Column(String, default="")
    status = Column(String, default="active")
    metadata_fields = Column(JSON, default=dict)  # named metadata_fields to avoid model conflicts


class SQLAnnotationRelationship(Base):
    __tablename__ = "annotation_relationships"

    id = Column(String, primary_key=True)
    source_annotation_id = Column(String, ForeignKey("annotations.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(String, nullable=False)
    target_kind = Column(String, nullable=False)  # "KG_NODE" or "ANNOTATION"
    relation_type = Column(String, nullable=False)
    properties = Column(JSON, default=dict)


class SQLAnnotationCollection(Base):
    __tablename__ = "annotation_collections"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    annotation_ids = Column(JSON, default=list)
