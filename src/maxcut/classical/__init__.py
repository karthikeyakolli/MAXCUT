"""Layer 3: Classical Reference Solver.

Provides verified ground-truth optimal cut calculations for benchmark comparisons.
"""

from maxcut.classical.solver import (
    ClassicalMaxCutResult,
    ExactExhaustiveSolver,
)

__all__ = [
    "ExactExhaustiveSolver",
    "ClassicalMaxCutResult",
]
