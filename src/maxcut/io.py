"""Official Challenge Kit input adapter and data ingestion module.

Adheres strictly to PROJECT_SPEC.md. Does not fabricate problem instances,
processor specs, or reference values.
"""

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import networkx as nx


class MissingChallengeKitArtifactError(FileNotFoundError):
    """Raised when an expected organizer Challenge Kit file is absent."""
    pass


class ChallengeKitValidationError(ValueError):
    """Raised when an organizer input file fails schema or integrity validation."""
    pass


@dataclass(frozen=True)
class MaxCutProblemInstance:
    """Formal domain representation of an organizer-provided Max-Cut problem instance."""

    name: str
    num_nodes: int
    num_edges: int
    nodes: List[int]
    edges: List[Tuple[int, int, float]]
    is_weighted: bool
    constraints: Dict[str, Any] = field(default_factory=dict)
    reference_optimum: Optional[float] = None
    optimal_bitstring: Optional[str] = None
    source_path: Optional[str] = None
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_networkx(self) -> nx.Graph:
        """Constructs an undirected NetworkX Graph from validated problem edges."""
        graph = nx.Graph()
        graph.add_nodes_from(self.nodes)
        for u, v, w in self.edges:
            graph.add_edge(u, v, weight=float(w))
        return graph

    def summary(self) -> str:
        """Returns a concise human-readable summary of the problem instance."""
        ref_str = f"{self.reference_optimum}" if self.reference_optimum is not None else "Unspecified in Challenge Kit"
        bitstring_str = f"'{self.optimal_bitstring}'" if self.optimal_bitstring else "Unspecified"
        return (
            f"Problem: {self.name}\n"
            f"Nodes (|V|): {self.num_nodes}\n"
            f"Edges (|E|): {self.num_edges}\n"
            f"Weighted: {self.is_weighted}\n"
            f"Reference Optimum (C_max): {ref_str}\n"
            f"Optimal Bitstring: {bitstring_str}\n"
            f"Constraints: {json.dumps(self.constraints)}\n"
            f"Source Path: {self.source_path or 'In-memory / Pending'}"
        )


@dataclass(frozen=True)
class ProcessorHardwareSpec:
    """Organizer-defined hardware specification for Processor A or Processor B."""

    name: str
    num_qubits: int
    coupling_map: List[Tuple[int, int]]
    basis_gates: List[str]
    qubit_properties: Dict[str, Any] = field(default_factory=dict)
    source_path: Optional[str] = None

    def summary(self) -> str:
        """Returns a concise summary of the hardware specification."""
        return (
            f"Processor: {self.name}\n"
            f"Qubits: {self.num_qubits}\n"
            f"Coupling Map Edges: {len(self.coupling_map)}\n"
            f"Basis Gates: {', '.join(self.basis_gates)}\n"
            f"Source Path: {self.source_path or 'Pending'}"
        )


def load_challenge_instance(file_path: Union[str, Path]) -> MaxCutProblemInstance:
    """Loads and validates a Max-Cut instance from an organizer-provided file.

    Supports JSON format (standard schema), adjacency matrix, or weighted edge list.
    Does NOT fabricate missing information.

    Args:
        file_path: Path to the challenge instance file.

    Returns:
        MaxCutProblemInstance: Validated problem instance.

    Raises:
        MissingChallengeKitArtifactError: If file_path does not exist.
        ChallengeKitValidationError: If data is malformed or invalid.
    """
    path = Path(file_path)
    if not path.exists():
        raise MissingChallengeKitArtifactError(
            f"Challenge Kit instance file not found at: '{path.resolve()}'. "
            "Please ensure the official organizer file is placed in 'instances/challenge/' "
            "or 'data/raw/' before loading."
        )

    # 1. Parse JSON format
    if path.suffix.lower() == ".json":
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise ChallengeKitValidationError(f"Invalid JSON in '{path}': {e}") from e

        return _parse_json_instance(data, source_path=str(path.resolve()))

    # 2. Parse text/edge-list format
    elif path.suffix.lower() in [".txt", ".edgelist", ".csv"]:
        return _parse_text_edge_list(path)

    else:
        raise ChallengeKitValidationError(
            f"Unsupported instance file format: '{path.suffix}'. "
            "Supported formats: .json, .txt, .edgelist, .csv"
        )


def _parse_json_instance(data: Dict[str, Any], source_path: str) -> MaxCutProblemInstance:
    """Parses and validates JSON challenge dictionary."""
    name = data.get("name", Path(source_path).stem)

    # Extract nodes
    if "nodes" in data:
        nodes = list(data["nodes"])
    elif "num_nodes" in data:
        nodes = list(range(int(data["num_nodes"])))
    else:
        # Infer nodes from edges if present
        all_edge_nodes = set()
        for edge in data.get("edges", []):
            all_edge_nodes.add(edge[0])
            all_edge_nodes.add(edge[1])
        nodes = sorted(list(all_edge_nodes)) if all_edge_nodes else []

    if not nodes:
        raise ChallengeKitValidationError(f"Instance '{name}' defines no graph nodes.")

    # Extract edges & weights
    raw_edges = data.get("edges", [])
    parsed_edges: List[Tuple[int, int, float]] = []
    is_weighted = False

    for item in raw_edges:
        if len(item) == 2:
            u, v = int(item[0]), int(item[1])
            w = 1.0
        elif len(item) >= 3:
            u, v, w = int(item[0]), int(item[1]), float(item[2])
            if w != 1.0:
                is_weighted = True
        else:
            raise ChallengeKitValidationError(f"Invalid edge entry in '{name}': {item}")

        if u == v:
            raise ChallengeKitValidationError(f"Self-loop detected on node {u} in '{name}'.")

        parsed_edges.append((u, v, w))

    constraints = data.get("constraints", {})
    ref_optimum = data.get("reference_optimum", data.get("optimal_cut_value", None))
    if ref_optimum is not None:
        ref_optimum = float(ref_optimum)
    optimal_bitstring = data.get("optimal_bitstring", None)

    return MaxCutProblemInstance(
        name=name,
        num_nodes=len(nodes),
        num_edges=len(parsed_edges),
        nodes=nodes,
        edges=parsed_edges,
        is_weighted=is_weighted,
        constraints=constraints,
        reference_optimum=ref_optimum,
        optimal_bitstring=optimal_bitstring,
        source_path=source_path,
        raw_metadata=data.get("metadata", {}),
    )


def _parse_text_edge_list(path: Path) -> MaxCutProblemInstance:
    """Parses edge list file (space, tab, or comma separated)."""
    edges: List[Tuple[int, int, float]] = []
    nodes_set = set()
    is_weighted = False

    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.replace(",", " ").split()
            if len(parts) == 2:
                u, v = int(parts[0]), int(parts[1])
                w = 1.0
            elif len(parts) >= 3:
                u, v, w = int(parts[0]), int(parts[1]), float(parts[2])
                if w != 1.0:
                    is_weighted = True
            else:
                raise ChallengeKitValidationError(
                    f"Malformed line {line_num} in '{path}': '{line}'"
                )

            if u == v:
                raise ChallengeKitValidationError(f"Self-loop on node {u} at line {line_num}.")

            nodes_set.add(u)
            nodes_set.add(v)
            edges.append((u, v, w))

    nodes = sorted(list(nodes_set))
    return MaxCutProblemInstance(
        name=path.stem,
        num_nodes=len(nodes),
        num_edges=len(edges),
        nodes=nodes,
        edges=edges,
        is_weighted=is_weighted,
        source_path=str(path.resolve()),
    )


def load_processor_spec(file_path: Union[str, Path]) -> ProcessorHardwareSpec:
    """Loads organizer hardware specification for Processor A or Processor B.

    Does not fabricate properties.

    Args:
        file_path: Path to the hardware spec JSON.

    Returns:
        ProcessorHardwareSpec: Validated hardware specification.

    Raises:
        MissingChallengeKitArtifactError: If file does not exist.
        ChallengeKitValidationError: If required fields are absent.
    """
    path = Path(file_path)
    if not path.exists():
        raise MissingChallengeKitArtifactError(
            f"Hardware specification not found at: '{path.resolve()}'."
        )

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for field_name in ["name", "num_qubits", "coupling_map", "basis_gates"]:
        if field_name not in data:
            raise ChallengeKitValidationError(
                f"Missing required field '{field_name}' in hardware spec '{path}'."
            )

    coupling_map = [tuple(edge) for edge in data["coupling_map"]]

    return ProcessorHardwareSpec(
        name=str(data["name"]),
        num_qubits=int(data["num_qubits"]),
        coupling_map=coupling_map,
        basis_gates=list(data["basis_gates"]),
        qubit_properties=data.get("qubit_properties", {}),
        source_path=str(path.resolve()),
    )
