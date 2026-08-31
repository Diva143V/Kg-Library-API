"""
Context Builder to format subgraphs, expert annotations, and external evidence into prompts.
"""

from kg_library_api.retrieval.retriever import MultiPerspectiveSearchResult


class ContextBuilder:
    """
    Constructs context text blocks for LLM reasoning prompts.
    """

    @staticmethod
    def build_prompt_context(search_res: MultiPerspectiveSearchResult) -> str:
        """Serializes retriever search results into a clean text block."""
        ctx_parts = []

        if search_res.knowledge_paths:
            ctx_parts.append("Base Knowledge Graph Paths:")
            for i, kp in enumerate(search_res.knowledge_paths):
                ctx_parts.append(f" Path {i+1}: {kp.get('formatted', '')}")

        if search_res.annotations:
            ctx_parts.append("Expert Annotations:")
            for ann in search_res.annotations:
                ctx_parts.append(
                    f" - [{ann['id']}] ({ann['type']}) by {ann.get('author', 'expert')}: "
                    f"'{ann['content']}' (Confidence: {ann.get('confidence', 1.0)})"
                )

        if search_res.annotation_paths:
            ctx_parts.append("Expert Annotation Relationships:")
            for ap in search_res.annotation_paths:
                if "target_annotation" in ap:
                    ctx_parts.append(
                        f" - Annotation {ap['source_annotation']} -({ap['relation_type']})-> "
                        f"Annotation {ap['target_annotation']}"
                    )
                else:
                    ctx_parts.append(
                        f" - Annotation {ap['source_annotation']} -({ap['relation_type']})-> "
                        f"KG Node {ap['target_entity']}"
                    )

        if search_res.evidence:
            ctx_parts.append("External Web/Domain Evidence:")
            for ev in search_res.evidence:
                source_label = ev.get('source_pack') or ev.get('source') or 'External'
                tool_label = f" via {ev.get('tool')}" if ev.get('tool') else ""
                ctx_parts.append(f" - [{source_label}{tool_label}]: '{ev['content']}'")

        return "\n".join(ctx_parts)
