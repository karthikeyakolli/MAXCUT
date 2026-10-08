"""Transparent classical parameter optimizer for QAOA Max-Cut.

Optimizes variational parameters (gamma, beta) using standard classical optimization
routines (e.g. COBYLA, SLSQP) with full audit tracking.
"""

from dataclasses import dataclass, field
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

import numpy as np
from qiskit.circuit import QuantumCircuit
from qiskit.quantum_info import Statevector
from scipy.optimize import minimize

from maxcut.domain.model import MaxCutGraph
from maxcut.formulation.qubo import QuantumCostHamiltonian, build_cost_hamiltonian
from maxcut.qaoa.ansatz import QAOAAnsatz, build_qaoa_circuit


@dataclass(frozen=True)
class QAOAOptimizationResult:
    """Detailed results from classical QAOA parameter optimization."""

    optimizer_name: str
    p: int
    optimal_gamma: List[float]
    optimal_beta: List[float]
    optimal_parameters: List[float]
    initial_parameters: List[float]
    num_evaluations: int
    final_objective_value: float
    final_expected_cut: float
    execution_time_seconds: float
    history: List[Dict[str, Any]] = field(default_factory=list)

    def summary(self) -> str:
        """Returns a clear summary of the QAOA parameter optimization."""
        gamma_str = ", ".join(f"{g:.4f}" for g in self.optimal_gamma)
        beta_str = ", ".join(f"{b:.4f}" for b in self.optimal_beta)
        return (
            f"=== QAOA Parameter Optimization (p={self.p}) ===\n"
            f"Optimizer: {self.optimizer_name}\n"
            f"Evaluations: {self.num_evaluations}\n"
            f"Execution Time: {self.execution_time_seconds:.4f} s\n"
            f"Final Energy (Objective): {self.final_objective_value:.4f}\n"
            f"Optimal Expected Cut <C>: {self.final_expected_cut:.4f}\n"
            f"Optimal Gamma: [{gamma_str}]\n"
            f"Optimal Beta:  [{beta_str}]\n"
        )


class QAOAOptimizer:
    """Classical optimization engine for QAOA parameter tuning."""

    def __init__(
        self,
        method: str = "COBYLA",
        maxiter: int = 100,
        tol: float = 1e-4,
        seed: int = 42,
    ) -> None:
        self.method: str = method
        self.maxiter: int = maxiter
        self.tol: float = tol
        self.seed: int = seed

    def optimize(
        self,
        graph: MaxCutGraph,
        p: int = 1,
        initial_point: Optional[Sequence[float]] = None,
    ) -> QAOAOptimizationResult:
        """Optimizes gamma and beta parameters for a given graph and depth p.

        Objective:
        E(gamma, beta) = <psi(gamma, beta)| H_C |psi(gamma, beta)>
        Minimizing E maximizes <C> = - E.

        Args:
            graph: MaxCutGraph domain instance.
            p: QAOA depth parameter.
            initial_point: Optional initial parameter vector of length 2p [gamma_0..p-1, beta_0..p-1].

        Returns:
            QAOAOptimizationResult: Complete optimization outcome with evaluation logs.
        """
        ansatz = build_qaoa_circuit(graph, p=p, include_measurements=False)
        hamiltonian = build_cost_hamiltonian(graph, include_offset=True)

        # Initialize parameters: p gammas in [0, 2*pi], p betas in [0, pi]
        if initial_point is None:
            rng = np.random.RandomState(self.seed)
            init_gamma = rng.uniform(0.0, 2.0 * np.pi, size=p)
            init_beta = rng.uniform(0.0, np.pi, size=p)
            init_params = np.concatenate([init_gamma, init_beta])
        else:
            if len(initial_point) != 2 * p:
                raise ValueError(
                    f"Initial point length ({len(initial_point)}) != 2*p ({2*p})."
                )
            init_params = np.array(initial_point, dtype=float)

        history: List[Dict[str, Any]] = []
        evaluation_count = 0

        def objective_function(params: np.ndarray) -> float:
            nonlocal evaluation_count
            evaluation_count += 1

            gamma_vals = params[:p]
            beta_vals = params[p:]

            bound_qc = ansatz.bind(gamma_vals, beta_vals)
            sv = Statevector(bound_qc)
            energy = sv.expectation_value(hamiltonian.cost_operator).real

            history.append({
                "step": evaluation_count,
                "gamma": [float(g) for g in gamma_vals],
                "beta": [float(b) for b in beta_vals],
                "energy": float(energy),
                "expected_cut": float(-energy),
            })
            return float(energy)

        start_time = time.perf_counter()

        options = {"maxiter": self.maxiter}
        if self.method.upper() == "COBYLA":
            options["tol"] = self.tol

        opt_res = minimize(
            fun=objective_function,
            x0=init_params,
            method=self.method,
            options=options,
        )

        elapsed_time = time.perf_counter() - start_time

        opt_params = opt_res.x
        opt_gamma = [float(g) for g in opt_params[:p]]
        opt_beta = [float(b) for b in opt_params[p:]]
        final_energy = float(opt_res.fun)
        final_expected_cut = float(-final_energy)

        return QAOAOptimizationResult(
            optimizer_name=self.method,
            p=p,
            optimal_gamma=opt_gamma,
            optimal_beta=opt_beta,
            optimal_parameters=[float(x) for x in opt_params],
            initial_parameters=[float(x) for x in init_params],
            num_evaluations=evaluation_count,
            final_objective_value=final_energy,
            final_expected_cut=final_expected_cut,
            execution_time_seconds=elapsed_time,
            history=history,
        )
