"""
Unit tests for Phase 3 — Annotation Model & Separate Annotation Storage.
"""

import pytest
from kg_library_api.annotations.models import Annotation, AnnotationType, AnnotationToKGRelationType
from kg_library_api.annotations.manager import AnnotationManager


def test_annotation_creation_and_fields():
    mgr = AnnotationManager()
    ann = mgr.create_annotation(
        type=AnnotationType.EVIDENCE.value,
        content="Trial 101 demonstrated 45% efficacy.",
        author="Dr. Smith",
        confidence=0.95,
        source="PubMed:345678",
        provenance="Clinical Trial Phase III",
    )

    assert ann.id is not None
    assert ann.type == "Evidence"
    assert ann.content == "Trial 101 demonstrated 45% efficacy."
    assert ann.author == "Dr. Smith"
    assert ann.confidence == 0.95
    assert ann.source == "PubMed:345678"
    assert ann.provenance == "Clinical Trial Phase III"
    assert ann.status == "active"


def test_annotation_relationships_and_entity_lookup():
    mgr = AnnotationManager()

    # Annotation A ABOUT Protein B
    ann_a = mgr.create_annotation(
        annotation_id="ann_a",
        type=AnnotationType.OBSERVATION.value,
        content="Protein B expression increases in disease tissue.",
    )

    mgr.add_annotation_relationship(
        source_annotation_id="ann_a",
        target_id="protein_b",
        relation_type=AnnotationToKGRelationType.ABOUT.value,
        target_kind="KG_NODE",
    )

    # Annotation A SUPPORTS Disease C
    mgr.add_annotation_relationship(
        source_annotation_id="ann_a",
        target_id="disease_c",
        relation_type=AnnotationToKGRelationType.SUPPORTS.value,
        target_kind="KG_NODE",
    )

    # Retrieve about protein_b
    about_b = mgr.get_annotations_about_entity("protein_b")
    assert len(about_b) == 1
    assert about_b[0]["annotation"]["id"] == "ann_a"
    assert about_b[0]["relationship"]["relation_type"] == "ABOUT"


def test_annotation_collections_and_subgraph():
    mgr = AnnotationManager()

    bulk_res = mgr.bulk_ingest_annotations(
        collection_id="expert_coll_1",
        annotations_data=[
            {"id": "a1", "type": "Assertion", "content": "Node X is key driver."},
            {"id": "a2", "type": "Correction", "content": "Correction to Node X mechanism."},
        ],
        relationships_data=[
            {
                "source_annotation_id": "a2",
                "target_id": "a1",
                "target_kind": "ANNOTATION",
                "relation_type": "CORRECTS",
            }
        ],
    )

    assert bulk_res["annotations_ingested"] == 2
    assert bulk_res["relationships_ingested"] == 1

    subgraph = mgr.get_annotation_subgraph(["a1"])
    assert len(subgraph["annotations"]) == 2
    assert len(subgraph["relationships"]) == 1
