"""Domain model for Max-Cut problems.

Defines robust representations for nodes, edges, weights, partitions,
cut values, and MaxCutGraph domain entities. Independent of UI and notebook code.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Set, Tuple, Union

import networkx as nx

from maxcut.io import (
    ChallengeKitValidationError,
    MaxCutProblemInstance,
    load_challenge_instance,
)


class InvalidAssignmentError(ValueError):
    """Raised when a partition assignment is invalid or fails vertex coverage."""
    pass


class GraphValidationError(ValueError):
    """Raised when graph definition violates structural or weight constraints."""
    pass


@dataclass(frozen=True)
class Edge:
    """An undirected edge between two vertices with a numerical weight."""

    u: int
    v: int
    weight: float = 1.0

    def __post_init__(self):
        if self.u == self.v:
            raise GraphValidationError(f"Self-loop detected on vertex {self.u}.")
        # Normalize canonical orientation (min(u, v), max(u, v)) for hashing & equality
        if self.u > self.v:
            min_node, max_node = self.v, self.u
            object.__setattr__(self, "u", min_node)
            object.__setattr__(self, "v", max_node)

    def endpoints(self) -> Tuple[int, int]:
        return self.u, self.v


@dataclass(frozen=True)
class Partition:
    """A 2-partition of graph vertices into set S and set not-S."""

    set_s: FrozenSet[int]
    set_not_s: FrozenSet[int]

    def is_complementary(self, other: "Partition") -> bool:
        """Checks if two partitions are complementary (represent identical cut)."""
        return (self.set_s == other.set_not_s and self.set_not_s == other.set_s) or (
            self.set_s == other.set_s and self.set_not_s == other.set_not_s
        )

    def to_assignment_dict(self) -> Dict[int, int]:
        """Converts partition to dictionary {node: 0/1} with S -> 1, not_S -> 0."""
        assignment = {node: 1 for node in self.set_s}
        assignment.update({node: 0 for node in self.set_not_s})
        return assignment


@dataclass(frozen=True)
class CutResult:
    """Result of evaluating a cut on a MaxCutGraph."""

    cut_value: float
    partition: Partition
    assignment: Dict[int, int]
    bitstring: str
    cut_edges: List[Edge]
    uncut_edges: List[Edge]
    total_graph_weight: float

    @property
    def num_cut_edges(self) -> int:
        return len(self.cut_edges)

    @property
    def cut_ratio(self) -> float:
        """Ratio of cut weight to total graph edge weight."""
        if self.total_graph_weight == 0:
            return 0.0
        return self.cut_value / self.total_graph_weight

    def summary(self) -> str:
        """Returns a human-readable solution summary."""
        set_s_sorted = sorted(list(self.partition.set_s))
        set_not_s_sorted = sorted(list(self.partition.set_not_s))
        return (
            f"=== Max-Cut Solution Evaluation ===\n"
            f"Cut Value: {self.cut_value:.4f} / Total Weight: {self.total_graph_weight:.4f}\n"
            f"Cut Ratio: {self.cut_ratio:.2%}\n"
            f"Cut Edges: {self.num_cut_edges} cut / {len(self.uncut_edges)} uncut\n"
            f"Bitstring (sorted node order): {self.bitstring}\n"
            f"Partition S (size {len(set_s_sorted)}): {set_s_sorted}\n"
            f"Partition ~S (size {len(set_not_s_sorted)}): {set_not_s_sorted}\n"
        )


class MaxCutGraph:
    """Core domain model representing a Max-Cut graph instance."""

    def __init__(
        self,
        nodes: Sequence[int],
        edges: Sequence[Union[Tuple[int, int], Tuple[int, int, float], Edge]],
        name: str = "MaxCutGraph",
    ) -> None:
        self.name: str = name
        raw_nodes = list(nodes)
        if len(raw_nodes) < 2:
            raise GraphValidationError(f"Graph '{name}' must contain at least 2 vertices.")

        # Ensure node uniqueness
        if len(set(raw_nodes)) != len(raw_nodes):
            raise GraphValidationError(f"Graph '{name}' contains duplicate node identifiers.")

        self._nodes: List[int] = sorted(raw_nodes)
        self._node_set: Set[int] = set(self._nodes)

        # Build canonical 0-based indexing map to support arbitrary node naming (e.g. 1-based)
        self._canonical_nodes: List[int] = list(range(len(self._nodes)))
        self._node_to_canonical: Dict[int, int] = {
            node: i for i, node in enumerate(self._nodes)
        }
        self._canonical_to_node: Dict[int, int] = {
            i: node for i, node in enumerate(self._nodes)
        }

        # Parse & normalize edges
        parsed_edges: List[Edge] = []
        is_weighted = False
        edge_pairs_seen = set()

        for item in edges:
            if isinstance(item, Edge):
                u, v, w = item.u, item.v, item.weight
            elif len(item) == 2:
                u, v = int(item[0]), int(item[1])
                w = 1.0
            elif len(item) >= 3:
                u, v, w = int(item[0]), int(item[1]), float(item[2])
                if w != 1.0:
                    is_weighted = True
            else:
                raise GraphValidationError(f"Invalid edge specification: {item}")

            if u not in self._node_set:
                raise GraphValidationError(f"Edge ({u}, {v}) references unknown node {u}.")
            if v not in self._node_set:
                raise GraphValidationError(f"Edge ({u}, {v}) references unknown node {v}.")
            if u == v:
                raise GraphValidationError(f"Self-loop detected on node {u}.")

            edge_key = (min(u, v), max(u, v))
            if edge_key in edge_pairs_seen:
                raise GraphValidationError(f"Duplicate edge detected between {u} and {v}.")
            edge_pairs_seen.add(edge_key)

            parsed_edges.append(Edge(u=u, v=v, weight=w))

        if not parsed_edges:
            raise GraphValidationError(f"Graph '{name}' has no edges.")

        self._edges: List[Edge] = parsed_edges
        self._is_weighted: bool = is_weighted
        self._total_weight: float = sum(e.weight for e in self._edges)

        # Internal NetworkX graph representation
        self._nx_graph: nx.Graph = nx.Graph()
        self._nx_graph.add_nodes_from(self._nodes)
        for e in self._edges:
            self._nx_graph.add_edge(e.u, e.v, weight=e.weight)

    # --- Properties ---

    @property
    def nodes(self) -> List[int]:
        """Sorted list of original node identifiers."""
        return list(self._nodes)

    @property
    def num_nodes(self) -> int:
        return len(self._nodes)

    @property
    def edges(self) -> List[Edge]:
        return list(self._edges)

    @property
    def num_edges(self) -> int:
        return len(self._edges)

    @property
    def is_weighted(self) -> bool:
        return self._is_weighted

    @property
    def total_weight(self) -> float:
        return self._total_weight

    @property
    def canonical_nodes(self) -> List[int]:
        """0-indexed canonical node indices [0, 1, ..., n-1]."""
        return list(self._canonical_nodes)

    def to_networkx(self) -> nx.Graph:
        """Returns a copy of the underlying NetworkX graph."""
        return self._nx_graph.copy()

    # --- Factory Class Methods ---

    @classmethod
    def from_edges(
        cls,
        edges: Sequence[Union[Tuple[int, int], Tuple[int, int, float], Edge]],
        nodes: Optional[Sequence[int]] = None,
        name: str = "MaxCutGraph",
    ) -> "MaxCutGraph":
        """Constructs MaxCutGraph from edge sequence, inferring nodes if omitted."""
        if nodes is None:
            inferred_nodes: Set[int] = set()
            for e in edges:
                if isinstance(e, Edge):
                    inferred_nodes.add(e.u)
                    inferred_nodes.add(e.v)
                else:
                    inferred_nodes.add(int(e[0]))
                    inferred_nodes.add(int(e[1]))
            node_seq = sorted(list(inferred_nodes))
        else:
            node_seq = list(nodes)

        return cls(nodes=node_seq, edges=edges, name=name)

    @classmethod
    def from_networkx(cls, graph: nx.Graph, name: Optional[str] = None) -> "MaxCutGraph":
        """Constructs MaxCutGraph from a NetworkX Graph instance."""
        graph_name = name or getattr(graph, "name", "FromNetworkX")
        nodes = [int(n) for n in graph.nodes()]
        edges = []
        for u, v, data in graph.edges(data=True):
            w = float(data.get("weight", 1.0))
            edges.append(Edge(u=int(u), v=int(v), weight=w))
        return cls(nodes=nodes, edges=edges, name=graph_name)

    @classmethod
    def from_challenge_instance(cls, instance: MaxCutProblemInstance) -> "MaxCutGraph":
        """Constructs MaxCutGraph directly from an ingested MaxCutProblemInstance."""
        return cls(
            nodes=instance.nodes,
            edges=instance.edges,
            name=instance.name,
        )

    @classmethod
    def from_challenge_file(cls, path: Union[str, Path]) -> "MaxCutGraph":
        """Loads and builds MaxCutGraph directly from an organizer Challenge Kit file."""
        instance = load_challenge_instance(path)
        return cls.from_challenge_instance(instance)

    # --- Validation & Assignment Handling ---

    def verify_assignment_coverage(
        self, assignment: Union[str, Sequence[int], Dict[int, int]]
    ) -> Dict[int, int]:
        """Validates that a binary assignment covers every required vertex.

        Supports:
        - Dict[node_id, 0/1]: Explicit mapping for each node.
        - Sequence[int] / str of length num_nodes: Assigned to nodes in sorted order.

        Returns:
            Dict[int, int]: Clean mapping from original node ID -> 0 or 1.

        Raises:
            InvalidAssignmentError: If assignment is malformed or vertices are missing.
        """
        if isinstance(assignment, dict):
            # Check for missing nodes
            missing = self._node_set - set(assignment.keys())
            if missing:
                raise InvalidAssignmentError(
                    f"Assignment missing vertices: {sorted(list(missing))}."
                )
            clean_map: Dict[int, int] = {}
            for node in self._nodes:
                val = assignment[node]
                if val not in (0, 1):
                    raise InvalidAssignmentError(
                        f"Assignment for node {node} must be 0 or 1, got {val}."
                    )
                clean_map[node] = int(val)
            return clean_map

        elif isinstance(assignment, (str, list, tuple)):
            if len(assignment) != self.num_nodes:
                raise InvalidAssignmentError(
                    f"Assignment length ({len(assignment)}) must equal graph vertex count ({self.num_nodes})."
                )
            clean_map = {}
            for i, node in enumerate(self._nodes):
                raw_val = assignment[i]
                if isinstance(raw_val, str):
                    if raw_val not in ("0", "1"):
                        raise InvalidAssignmentError(
                            f"Invalid character '{raw_val}' in bitstring at index {i}."
                        )
                    val = int(raw_val)
                elif isinstance(raw_val, int):
                    if raw_val not in (0, 1):
                        raise InvalidAssignmentError(
                            f"Invalid value {raw_val} at index {i}. Expected 0 or 1."
                        )
                    val = raw_val
                else:
                    raise InvalidAssignmentError(f"Unsupported assignment element: {type(raw_val)}")

                clean_map[node] = val
            return clean_map

        else:
            raise InvalidAssignmentError(f"Unsupported assignment type: {type(assignment)}")

    def assignment_to_partition(
        self, assignment: Union[str, Sequence[int], Dict[int, int]]
    ) -> Partition:
        """Converts a valid binary assignment into two partitions (Set S and Set ~S)."""
        clean_map = self.verify_assignment_coverage(assignment)
        set_s = frozenset(node for node, val in clean_map.items() if val == 1)
        set_not_s = frozenset(node for node, val in clean_map.items() if val == 0)
        return Partition(set_s=set_s, set_not_s=set_not_s)

    def compute_cut(
        self, assignment: Union[str, Sequence[int], Dict[int, int]]
    ) -> CutResult:
        """Computes the cut value of a given binary assignment.

        Cut value C(x) = sum_{(u,v) in E} w_{uv} * (x_u XOR x_v).

        Args:
            assignment: Binary assignment (dict, sequence of ints, or bitstring).

        Returns:
            CutResult: Comprehensive evaluation object containing cut value,
                       partitions, cut edges, and uncut edges.
        """
        clean_map = self.verify_assignment_coverage(assignment)
        partition = self.assignment_to_partition(clean_map)

        cut_edges: List[Edge] = []
        uncut_edges: List[Edge] = []
        cut_value: float = 0.0

        for edge in self._edges:
            val_u = clean_map[edge.u]
            val_v = clean_map[edge.v]
            if val_u != val_v:
                cut_value += edge.weight
                cut_edges.append(edge)
            else:
                uncut_edges.append(edge)

        # Canonical bitstring ordered by sorted node IDs
        bitstring = "".join(str(clean_map[node]) for node in self._nodes)

        return CutResult(
            cut_value=cut_value,
            partition=partition,
            assignment=clean_map,
            bitstring=bitstring,
            cut_edges=cut_edges,
            uncut_edges=uncut_edges,
            total_graph_weight=self._total_weight,
        )

    def summary(self) -> str:
        """Returns a clear, human-readable summary of the graph structure."""
        degrees = [d for _, d in self._nx_graph.degree()]
        min_deg = min(degrees) if degrees else 0
        max_deg = max(degrees) if degrees else 0
        avg_deg = sum(degrees) / len(degrees) if degrees else 0.0
        connected = nx.is_connected(self._nx_graph)

        return (
            f"=== MaxCutGraph: {self.name} ===\n"
            f"Vertices (|V|): {self.num_nodes} (Node IDs: {self._nodes[:8]}{'...' if len(self._nodes) > 8 else ''})\n"
            f"Edges (|E|): {self.num_edges}\n"
            f"Total Weight: {self._total_weight:.4f}\n"
            f"Weighted: {self._is_weighted}\n"
            f"Connected: {connected}\n"
            f"Degree (min/avg/max): {min_deg} / {avg_deg:.2f} / {max_deg}\n"
        )
