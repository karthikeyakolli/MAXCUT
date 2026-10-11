"""Factory function for creating simulator or hardware processor backend runners."""

from pathlib import Path
from typing import Any, Dict, Optional, Union

from maxcut.backends.aer_backend import AerBackendRunner
from maxcut.backends.base import BaseBackendRunner
from maxcut.backends.processor_backend import ProcessorBackendRunner
from maxcut.io import ProcessorHardwareSpec


def create_backend_runner(
    backend_name: str = "aer_simulator",
    hardware_spec: Optional[Union[ProcessorHardwareSpec, str, Path]] = None,
    seed_simulator: int = 42,
    seed_transpiler: int = 42,
    execution_mode: str = "ideal",
    noise_config: Optional[Dict[str, Any]] = None,
) -> BaseBackendRunner:
    """Instantiates a standardized backend runner.

    Args:
        backend_name: Identifier for backend ('aer_simulator', 'processor_a', 'processor_b').
        hardware_spec: Optional hardware specification or path to spec JSON.
        seed_simulator: RNG seed for shot simulation.
        seed_transpiler: RNG seed for circuit compilation/routing.
        execution_mode: 'ideal' or 'noisy'.
        noise_config: Optional noise parameter dictionary.

    Returns:
        BaseBackendRunner: Configured backend runner instance.
    """
    clean_name = backend_name.lower().replace("-", "_")

    if clean_name in ["aer", "aer_simulator", "simulator", "ideal_aer"]:
        return AerBackendRunner(
            seed_simulator=seed_simulator,
            seed_transpiler=seed_transpiler,
            backend_name="aer_simulator",
        )

    if clean_name == "processor_a":
        from processors.processor_a.adapter import ProcessorABackend
        spec_path = hardware_spec if isinstance(hardware_spec, (str, Path)) else None
        return ProcessorABackend(
            spec_path=Path(spec_path) if spec_path else None,
            seed_simulator=seed_simulator,
            seed_transpiler=seed_transpiler,
            execution_mode=execution_mode,
            noise_config=noise_config,
        )

    if clean_name == "processor_b":
        from processors.processor_b.adapter import ProcessorBBackend
        spec_path = hardware_spec if isinstance(hardware_spec, (str, Path)) else None
        return ProcessorBBackend(
            spec_path=Path(spec_path) if spec_path else None,
            seed_simulator=seed_simulator,
            seed_transpiler=seed_transpiler,
            execution_mode=execution_mode,
            noise_config=noise_config,
        )

    # Generic processor fallback
    spec_obj: Optional[Union[ProcessorHardwareSpec, str, Path]] = hardware_spec
    if spec_obj is None:
        candidate_path = Path("data/hardware_specs") / f"{clean_name}.json"
        if candidate_path.exists():
            spec_obj = candidate_path

    if spec_obj is None:
        raise ValueError(
            f"Hardware specification must be provided for processor backend '{backend_name}'. "
            f"Provide a ProcessorHardwareSpec object or ensure '{clean_name}.json' exists in 'data/hardware_specs/'."
        )

    return ProcessorBackendRunner(
        spec=spec_obj,
        seed_simulator=seed_simulator,
        seed_transpiler=seed_transpiler,
        execution_mode=execution_mode,
        noise_config=noise_config,
    )
