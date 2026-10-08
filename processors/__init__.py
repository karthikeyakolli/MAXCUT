"""Target hardware processors package."""

from processors.processor_a.adapter import ProcessorABackend
from processors.processor_b.adapter import ProcessorBBackend

__all__ = ["ProcessorABackend", "ProcessorBBackend"]
