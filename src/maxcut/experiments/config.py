"""Common experiment configuration dataclass for reproducible QAOA runs."""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class ExperimentConfig:
    """Standardized configuration for QAOA Max-Cut experiments across simulator and hardware."""

    # Problem instance specification
    graph_name: str = "O1_MaxCut_Challenge"
    problem_instance_path: Optional[str] = "instances/challenge/o1_maxcut_instance.json"

    # QAOA algorithmic parameters
    depth_p: int = 1
    shots: int = 2048
    optimizer: str = "COBYLA"
    initial_parameters: Optional[List[float]] = None
    optimization_settings: Dict[str, Any] = field(
        default_factory=lambda: {"max_iterations": 100, "tolerance": 1e-4}
    )

    # Random seeds for reproducibility
    random_seeds: Dict[str, int] = field(
        default_factory=lambda: {
            "seed_global": 42,
            "seed_simulator": 42,
            "seed_transpiler": 42,
        }
    )

    # Backend / Target target selection
    backend_name: str = "aer_simulator"
    transpilation_level: int = 1
    hardware_spec_path: Optional[str] = None

    # Classical reference ground truth
    classical_reference_path: Optional[str] = "results/data/classical_reference.json"

    # Output storage
    output_location: str = "results/data"

    def to_dict(self) -> Dict[str, Any]:
        """Converts configuration to a standard dictionary."""
        return asdict(self)

    def to_json(self, file_path: Union[str, Path], indent: int = 2) -> None:
        """Serializes configuration to a JSON file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentConfig":
        """Instantiates ExperimentConfig from a dictionary."""
        allowed_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in allowed_keys}
        return cls(**filtered)

    @classmethod
    def from_json(cls, file_path: Union[str, Path]) -> "ExperimentConfig":
        """Loads ExperimentConfig from a JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found at: '{path.resolve()}'")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
