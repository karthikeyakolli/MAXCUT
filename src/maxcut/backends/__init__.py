"""Backend abstraction layer for local simulator and target hardware execution."""

from maxcut.backends.aer_backend import AerBackendRunner, AerExecutionResult
from maxcut.backends.base import BackendExecutionResult, BaseBackendRunner
from maxcut.backends.factory import create_backend_runner
from maxcut.backends.processor_backend import (
    ProcessorBackendRunner,
    ProcessorExecutionResult,
)

__all__ = [
    "BaseBackendRunner",
    "BackendExecutionResult",
    "AerBackendRunner",
    "AerExecutionResult",
    "ProcessorBackendRunner",
    "ProcessorExecutionResult",
    "create_backend_runner",
]
