"""
Deterministic program code-based graph traversal engine for Polaris.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from collections import deque
from dataclasses import dataclass, field
from polaris_kg.core.models import Node, Relationship, Subgraph
from polaris_kg.core.kg import KnowledgeGraph


@dataclass
class TraversalPath:
    """Represents a deterministic path traversed through the knowledge graph."""
    nodes: List[Node]
    relationships: List[Relationship]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "relationships": [r.to_dict() for r in self.relationships],
            "formatted": " -> ".join(
                f"[{self.nodes[i].id}] -({self.relationships[i].type})->"
                for i in range(len(self.relationships))
            ) + (f" [{self.nodes[-1].id}]" if self.nodes else "")
        }


@dataclass
class TraversalResult:
    """Contains the results of a deterministic traversal execution."""
    start_nodes: List[str]
    paths: List[TraversalPath] = field(default_factory=list)
    visited_node_ids: List[str] = field(default_factory=list)
    traversed_relationship_ids: List[str] = field(default_factory=list)
    subgraph: Optional[Subgraph] = None
    nodes_count: int = 0
    edges_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_nodes": self.start_nodes,
            "paths": [p.to_dict() for p in self.paths],
            "visited_node_ids": self.visited_node_ids,
            "traversed_relationship_ids": self.traversed_relationship_ids,
            "subgraph": self.subgraph.to_dict() if self.subgraph else {"nodes": [], "relationships": []},
            "nodes_count": self.nodes_count,
            "edges_count": self.edges_count,
        }


class DeterministicTraversalEngine:
    """
    Executes 100% deterministic code-driven graph traversal algorithms (BFS, DFS, k-hop).
    Does NOT depend on LLMs to select nodes or edges.
    """

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg

    def traverse(
        self,
        start_nodes: List[str],
        algorithm: str = "bfs",
        max_depth: int = 3,
        relationship_types: Optional[List[str]] = None,
        node_labels: Optional[List[str]] = None,
        max_nodes: Optional[int] = None,
        directed: bool = True,
        traversal_mode: str = "manual",  # "manual" (deterministic code) or "ai" (LLM-driven)
        llm: Optional[Any] = None,
    ) -> TraversalResult:
        """
        Main traversal entry point.
        
        Args:
            start_nodes: List of starting node IDs.
            algorithm: 'bfs', 'dfs', or 'k_hop'.
            max_depth: Maximum search depth.
            relationship_types: Optional whitelist of relationship types to follow.
            node_labels: Optional whitelist of node labels to include.
            max_nodes: Optional limit on maximum visited nodes.
            directed: Whether to respect edge direction (source -> target).
            traversal_mode: 'manual' (deterministic program code) or 'ai' (LLM-guided step selection).
            llm: Optional LLM instance for 'ai' traversal mode.
        """
        if traversal_mode.lower() == "ai":
            return self.ai_traverse(
                start_nodes=start_nodes,
                max_depth=max_depth,
                relationship_types=relationship_types,
                node_labels=node_labels,
                max_nodes=max_nodes,
                directed=directed,
                llm=llm,
            )

        algo = algorithm.lower()
        if algo == "bfs":
            return self.bfs(
                start_nodes=start_nodes,
                max_depth=max_depth,
                relationship_types=relationship_types,
                node_labels=node_labels,
                max_nodes=max_nodes,
                directed=directed,
            )
        elif algo == "dfs":
            return self.dfs(
                start_nodes=start_nodes,
                max_depth=max_depth,
                relationship_types=relationship_types,
                node_labels=node_labels,
                max_nodes=max_nodes,
                directed=directed,
            )
        elif algo == "k_hop":
            return self.k_hop(
                start_nodes=start_nodes,
                k=max_depth,
                relationship_types=relationship_types,
                node_labels=node_labels,
                max_nodes=max_nodes,
                directed=directed,
            )
        else:
            raise ValueError(f"Unsupported traversal algorithm: {algorithm}. Choose 'bfs', 'dfs', or 'k_hop'.")

    def ai_traverse(
        self,
        start_nodes: List[str],
        max_depth: int = 3,
        relationship_types: Optional[List[str]] = None,
        node_labels: Optional[List[str]] = None,
        max_nodes: Optional[int] = None,
        directed: bool = True,
        llm: Optional[Any] = None,
    ) -> TraversalResult:
        """
        AI-driven graph traversal mode: uses LLM scoring/pruning to choose candidate edges at each step.
        """
        visited_nodes: Set[str] = set()
        visited_rels: Set[str] = set()
        paths: List[TraversalPath] = []

        sorted_start_nodes = sorted([s for s in start_nodes if self.kg.get_node(s)])
        queue = deque()
        for snid in sorted_start_nodes:
            start_node = self.kg.get_node(snid)
            if start_node:
                visited_nodes.add(snid)
                queue.append((start_node, [start_node], [], 0))

        while queue:
            if max_nodes and len(visited_nodes) >= max_nodes:
                break

            curr_node, path_nodes, path_rels, depth = queue.popleft()

            if path_rels:
                paths.append(TraversalPath(nodes=list(path_nodes), relationships=list(path_rels)))

            if depth >= max_depth:
                continue

            neighbors = self._get_valid_outbound_relationships(
                curr_node.id,
                relationship_types=relationship_types,
                node_labels=node_labels,
                directed=directed,
            )

            if not neighbors:
                continue

            # LLM Edge Selection & Pruning Step
            selected_neighbors = self._select_edges_with_llm(curr_node, neighbors, llm)

            for rel, neighbor in selected_neighbors:
                if neighbor.id in [n.id for n in path_nodes]:
                    continue

                visited_nodes.add(neighbor.id)
                visited_rels.add(rel.id)

                new_path_nodes = path_nodes + [neighbor]
                new_path_rels = path_rels + [rel]

                queue.append((neighbor, new_path_nodes, new_path_rels, depth + 1))

        nodes_list = [self.kg.get_node(nid) for nid in sorted(visited_nodes) if self.kg.get_node(nid)]
        rels_list = [rel for rid in sorted(visited_rels) for rel in self.kg.get_relationships() if rel.id == rid]

        subgraph = Subgraph(nodes=nodes_list, relationships=rels_list)

        return TraversalResult(
            start_nodes=sorted_start_nodes,
            paths=paths,
            visited_node_ids=sorted(list(visited_nodes)),
            traversed_relationship_ids=sorted(list(visited_rels)),
            subgraph=subgraph,
            nodes_count=len(visited_nodes),
            edges_count=len(visited_rels),
        )

    def _select_edges_with_llm(
        self, curr_node: Node, candidate_tuples: List[Tuple[Relationship, Node]], llm: Optional[Any] = None
    ) -> List[Tuple[Relationship, Node]]:
        """LLM-driven edge selection helper."""
        if llm and hasattr(llm, "generate"):
            try:
                candidate_str = "\n".join(
                    f"- Edge {r.id}: {curr_node.id} -({r.type})-> {n.id} ({n.label})"
                    for r, n in candidate_tuples
                )
                prompt = f"Given node '{curr_node.id}', select the best edges to follow:\n{candidate_str}"
                resp = str(llm.generate([{"role": "user", "content": prompt}]))
                # Filter candidates mentioned in LLM response
                selected = [
                    (r, n) for r, n in candidate_tuples
                    if r.id in resp or n.id in resp or r.type in resp
                ]
                if selected:
                    return selected
            except Exception:
                pass
        # Fallback for AI mode: return top 2 candidates
        return candidate_tuples[:2]

    def _get_valid_outbound_relationships(
        self,
        node_id: str,
        relationship_types: Optional[List[str]] = None,
        node_labels: Optional[List[str]] = None,
        directed: bool = True,
    ) -> List[Tuple[Relationship, Node]]:
        """Find matching relationships and target nodes originating from or connected to node_id."""
        results = []
        # Get all relationships connected to node_id
        if directed:
            out_rels = self.kg.get_relationships(source_id=node_id)
        else:
            out_rels = self.kg.get_relationships(source_id=node_id) + self.kg.get_relationships(target_id=node_id)

        # Sort relationships deterministically by ID
        out_rels.sort(key=lambda r: r.id)

        for rel in out_rels:
            if relationship_types and rel.type not in relationship_types:
                continue
            
            neighbor_id = rel.target_id if rel.source_id == node_id else rel.source_id
            neighbor_node = self.kg.get_node(neighbor_id)

            if not neighbor_node:
                continue

            if node_labels and neighbor_node.label not in node_labels:
                continue

            results.append((rel, neighbor_node))

        return results

    def bfs(
        self,
        start_nodes: List[str],
        max_depth: int = 3,
        relationship_types: Optional[List[str]] = None,
        node_labels: Optional[List[str]] = None,
        max_nodes: Optional[int] = None,
        directed: bool = True,
    ) -> TraversalResult:
        """Deterministically traverse graph using Breadth-First Search (BFS)."""
        visited_nodes: Set[str] = set()
        visited_rels: Set[str] = set()
        paths: List[TraversalPath] = []

        # Sort start_nodes for deterministic order
        sorted_start_nodes = sorted([s for s in start_nodes if self.kg.get_node(s)])

        # Queue storing tuples of: (current_node, current_path_nodes, current_path_rels, depth)
        queue = deque()
        for snid in sorted_start_nodes:
            start_node = self.kg.get_node(snid)
            if start_node:
                visited_nodes.add(snid)
                queue.append((start_node, [start_node], [], 0))

        while queue:
            if max_nodes and len(visited_nodes) >= max_nodes:
                break

            curr_node, path_nodes, path_rels, depth = queue.popleft()

            if path_rels:
                paths.append(TraversalPath(nodes=list(path_nodes), relationships=list(path_rels)))

            if depth >= max_depth:
                continue

            neighbors = self._get_valid_outbound_relationships(
                curr_node.id,
                relationship_types=relationship_types,
                node_labels=node_labels,
                directed=directed,
            )

            for rel, neighbor in neighbors:
                # Cycle prevention in current path
                if neighbor.id in [n.id for n in path_nodes]:
                    continue

                visited_nodes.add(neighbor.id)
                visited_rels.add(rel.id)

                new_path_nodes = path_nodes + [neighbor]
                new_path_rels = path_rels + [rel]

                queue.append((neighbor, new_path_nodes, new_path_rels, depth + 1))

        nodes_list = [self.kg.get_node(nid) for nid in sorted(visited_nodes) if self.kg.get_node(nid)]
        rels_list = [rel for rid in sorted(visited_rels) for rel in self.kg.get_relationships() if rel.id == rid]

        subgraph = Subgraph(nodes=nodes_list, relationships=rels_list)

        return TraversalResult(
            start_nodes=sorted_start_nodes,
            paths=paths,
            visited_node_ids=sorted(list(visited_nodes)),
            traversed_relationship_ids=sorted(list(visited_rels)),
            subgraph=subgraph,
            nodes_count=len(visited_nodes),
            edges_count=len(visited_rels),
        )

    def dfs(
        self,
        start_nodes: List[str],
        max_depth: int = 3,
        relationship_types: Optional[List[str]] = None,
        node_labels: Optional[List[str]] = None,
        max_nodes: Optional[int] = None,
        directed: bool = True,
    ) -> TraversalResult:
        """Deterministically traverse graph using Depth-First Search (DFS)."""
        visited_nodes: Set[str] = set()
        visited_rels: Set[str] = set()
        paths: List[TraversalPath] = []

        sorted_start_nodes = sorted([s for s in start_nodes if self.kg.get_node(s)])

        def _dfs_visit(curr_node: Node, path_nodes: List[Node], path_rels: List[Relationship], depth: int):
            if max_nodes and len(visited_nodes) >= max_nodes:
                return

            visited_nodes.add(curr_node.id)

            if path_rels:
                paths.append(TraversalPath(nodes=list(path_nodes), relationships=list(path_rels)))

            if depth >= max_depth:
                return

            neighbors = self._get_valid_outbound_relationships(
                curr_node.id,
                relationship_types=relationship_types,
                node_labels=node_labels,
                directed=directed,
            )

            for rel, neighbor in neighbors:
                if neighbor.id in [n.id for n in path_nodes]:
                    continue

                visited_rels.add(rel.id)
                _dfs_visit(
                    curr_node=neighbor,
                    path_nodes=path_nodes + [neighbor],
                    path_rels=path_rels + [rel],
                    depth=depth + 1,
                )

        for snid in sorted_start_nodes:
            start_node = self.kg.get_node(snid)
            if start_node:
                _dfs_visit(start_node, [start_node], [], 0)

        nodes_list = [self.kg.get_node(nid) for nid in sorted(visited_nodes) if self.kg.get_node(nid)]
        rels_list = [rel for rid in sorted(visited_rels) for rel in self.kg.get_relationships() if rel.id == rid]

        subgraph = Subgraph(nodes=nodes_list, relationships=rels_list)

        return TraversalResult(
            start_nodes=sorted_start_nodes,
            paths=paths,
            visited_node_ids=sorted(list(visited_nodes)),
            traversed_relationship_ids=sorted(list(visited_rels)),
            subgraph=subgraph,
            nodes_count=len(visited_nodes),
            edges_count=len(visited_rels),
        )

    def k_hop(
        self,
        start_nodes: List[str],
        k: int = 2,
        relationship_types: Optional[List[str]] = None,
        node_labels: Optional[List[str]] = None,
        max_nodes: Optional[int] = None,
        directed: bool = True,
    ) -> TraversalResult:
        """Deterministically extract all nodes and paths within exactly k hops."""
        return self.bfs(
            start_nodes=start_nodes,
            max_depth=k,
            relationship_types=relationship_types,
            node_labels=node_labels,
            max_nodes=max_nodes,
            directed=directed,
        )
