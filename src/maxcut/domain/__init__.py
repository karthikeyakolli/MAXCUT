"""Layer 2: Max-Cut Domain Model.

Encapsulates graph structures, node/edge attributes, partitions,
and classical cut evaluation logic.
"""

from maxcut.domain.model import (
    CutResult,
    Edge,
    GraphValidationError,
    InvalidAssignmentError,
    MaxCutGraph,
    Partition,
)

__all__ = [
    "Edge",
    "Partition",
    "CutResult",
    "MaxCutGraph",
    "InvalidAssignmentError",
    "GraphValidationError",
]
