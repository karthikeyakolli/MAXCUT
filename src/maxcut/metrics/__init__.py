"""Layer 8: Metrics calculation & persistence.

Calculates resource consumption, circuit metrics, and comparative tables.
"""

from maxcut.metrics.circuit_metrics import (
    CircuitResourceMetrics,
    extract_circuit_metrics,
)
from maxcut.metrics.comparator import ProcessorCircuitComparator

__all__ = [
    "CircuitResourceMetrics",
    "extract_circuit_metrics",
    "ProcessorCircuitComparator",
]
