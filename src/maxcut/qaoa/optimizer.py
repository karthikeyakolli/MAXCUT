"""Transparent classical parameter optimizer for QAOA Max-Cut.

Optimizes variational parameters (gamma, beta) using standard classical optimization
routines (e.g. COBYLA, SLSQP) with full audit tracking.
"""

from dataclasses import asdict, dataclass, field
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
from qiskit.circuit import QuantumCircuit
from qiskit.quantum_info import Statevector
from scipy.optimize import minimize

from maxcut.domain.model import MaxCutGraph
from maxcut.formulation.qubo import (
    QuantumCostHamiltonian,
    build_cost_hamiltonian,
    build_reduced_cost_hamiltonian,
)
from maxcut.qaoa.ansatz import (
    QAOAAnsatz,
    build_qaoa_circuit,
    build_reduced_qaoa_circuit,
)


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
    converged: bool = True
    message: str = "Optimization completed successfully."

    def to_dict(self) -> Dict[str, Any]:
        """Serializes result to a dictionary."""
        return asdict(self)

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
            f"Converged: {self.converged} ({self.message})\n"
        )


@dataclass(frozen=True)
class QAOAMultistartResult:
    """Audit-compliant container for multistart QAOA parameter optimization results."""

    optimizer_name: str
    p: int
    num_restarts: int
    selected_restart_index: int
    optimal_gamma: List[float]
    optimal_beta: List[float]
    optimal_parameters: List[float]
    best_objective_value: float  # Minimization energy E = - <C>
    best_expected_cut: float     # Maximization cut <C>
    total_evaluations: int
    total_execution_time_seconds: float
    restarts: List[Dict[str, Any]] = field(default_factory=list)
    formulation: str = "standard_6q"

    def to_dict(self) -> Dict[str, Any]:
        """Serializes multistart results to dictionary."""
        return asdict(self)

    def summary(self) -> str:
        """Returns human-readable summary table of multistart restarts."""
        gamma_str = ", ".join(f"{g:.6f}" for g in self.optimal_gamma)
        beta_str = ", ".join(f"{b:.6f}" for b in self.optimal_beta)
        lines = [
            f"=== QAOA Multistart Optimization (p={self.p}, {self.num_restarts} Restarts) ===",
            f"Formulation: {self.formulation}",
            f"Optimizer: {self.optimizer_name}",
            f"Total Evaluations across Restarts: {self.total_evaluations}",
            f"Total Execution Time: {self.total_execution_time_seconds:.4f} s",
            f"Selected Best Restart: #{self.selected_restart_index + 1}",
            f"Global Best Energy: {self.best_objective_value:.6f}",
            f"Global Best Expected Cut <C>: {self.best_expected_cut:.6f}",
            f"Optimal Gamma*: [{gamma_str}] rad",
            f"Optimal Beta*:  [{beta_str}] rad",
            "",
            "Restart Audit Table:",
            f"{'ID':>4} | {'Seed':>6} | {'Init Params':>24} | {'Opt Params':>24} | {'Energy':>10} | {'<C>':>8} | {'Evals':>6} | {'Status'}",
            "-" * 105,
        ]
        for r in self.restarts:
            init_str = f"[{', '.join(f'{x:.3f}' for x in r['initial_parameters'])}]"
            opt_str = f"[{', '.join(f'{x:.3f}' for x in r['optimal_parameters'])}]"
            selected_flag = " *" if r["restart_index"] == self.selected_restart_index else ""
            lines.append(
                f"{r['restart_index'] + 1:>4} | {r['seed']:>6} | {init_str:>24} | {opt_str:>24} | "
                f"{r['final_objective_value']:>10.4f} | {r['final_expected_cut']:>8.4f} | "
                f"{r['num_evaluations']:>6} | {'Converged' if r['converged'] else 'MaxIter'}{selected_flag}"
            )
        return "\n".join(lines)


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
        use_reduced: bool = False,
        fixed_node: int = 0,
    ) -> QAOAOptimizationResult:
        """Optimizes gamma and beta parameters for a given graph and depth p.

        Objective:
        E(gamma, beta) = <psi(gamma, beta)| H_C |psi(gamma, beta)>
        Minimizing E maximizes <C> = - E.

        Args:
            graph: MaxCutGraph domain instance.
            p: QAOA depth parameter.
            initial_point: Optional initial parameter vector of length 2p [gamma_0..p-1, beta_0..p-1].
            use_reduced: Whether to use the 5-qubit symmetry-reduced formulation.
            fixed_node: Node fixed to 0 in symmetry reduction (default 0).

        Returns:
            QAOAOptimizationResult: Complete optimization outcome with evaluation logs.
        """
        if use_reduced:
            ansatz = build_reduced_qaoa_circuit(
                graph, p=p, fixed_node=fixed_node, include_measurements=False
            )
            hamiltonian = build_reduced_cost_hamiltonian(
                graph, fixed_node=fixed_node, include_offset=True
            )
        else:
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

        options: Dict[str, Any] = {"maxiter": self.maxiter}
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
        converged = bool(opt_res.success) if hasattr(opt_res, "success") else True
        message = str(opt_res.message) if hasattr(opt_res, "message") else "Done"

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
            converged=converged,
            message=message,
        )

    def optimize_multistart(
        self,
        graph: MaxCutGraph,
        p: int = 1,
        num_restarts: int = 10,
        base_seed: int = 42,
        use_reduced: bool = False,
        fixed_node: int = 0,
    ) -> QAOAMultistartResult:
        """Executes deterministic multistart classical QAOA parameter optimization.

        Iterates across `num_restarts` independent initial parameter vectors generated
        from deterministic seeds (base_seed + i). Tracks complete audit metadata
        for each restart and selects parameters that achieve global minimal energy.

        Args:
            graph: MaxCutGraph domain instance.
            p: QAOA depth parameter (default 1).
            num_restarts: Total number of restarts (default 10).
            base_seed: Base integer seed for reproducibility.
            use_reduced: Whether to use 5-qubit symmetry reduction.
            fixed_node: Reference vertex for symmetry reduction.

        Returns:
            QAOAMultistartResult: Audit-compliant container with all restart runs and best params.
        """
        start_time_all = time.perf_counter()
        restarts_list: List[Dict[str, Any]] = []
        total_evals = 0
        best_idx = 0
        best_energy = float("inf")

        formulation_label = "5_qubit_symmetry_reduced" if use_reduced else "standard_6q"

        for i in range(num_restarts):
            seed_i = base_seed + i
            rng_i = np.random.RandomState(seed_i)
            init_gamma = rng_i.uniform(0.0, 2.0 * np.pi, size=p)
            init_beta = rng_i.uniform(0.0, np.pi, size=p)
            init_pt = np.concatenate([init_gamma, init_beta])

            single_res = self.optimize(
                graph=graph,
                p=p,
                initial_point=init_pt,
                use_reduced=use_reduced,
                fixed_node=fixed_node,
            )

            total_evals += single_res.num_evaluations

            restart_record = {
                "restart_index": i,
                "seed": seed_i,
                "initial_parameters": [float(x) for x in single_res.initial_parameters],
                "optimal_parameters": [float(x) for x in single_res.optimal_parameters],
                "optimal_gamma": [float(x) for x in single_res.optimal_gamma],
                "optimal_beta": [float(x) for x in single_res.optimal_beta],
                "final_objective_value": float(single_res.final_objective_value),
                "final_expected_cut": float(single_res.final_expected_cut),
                "num_evaluations": single_res.num_evaluations,
                "execution_time_seconds": single_res.execution_time_seconds,
                "converged": single_res.converged,
                "message": single_res.message,
            }
            restarts_list.append(restart_record)

            if single_res.final_objective_value < best_energy:
                best_energy = single_res.final_objective_value
                best_idx = i

        total_elapsed = time.perf_counter() - start_time_all
        best_record = restarts_list[best_idx]

        return QAOAMultistartResult(
            optimizer_name=self.method,
            p=p,
            num_restarts=num_restarts,
            selected_restart_index=best_idx,
            optimal_gamma=best_record["optimal_gamma"],
            optimal_beta=best_record["optimal_beta"],
            optimal_parameters=best_record["optimal_parameters"],
            best_objective_value=best_record["final_objective_value"],
            best_expected_cut=best_record["final_expected_cut"],
            total_evaluations=total_evals,
            total_execution_time_seconds=total_elapsed,
            restarts=restarts_list,
            formulation=formulation_label,
        )
