from processors.processor_a.adapter import ProcessorABackend
from processors.processor_b.adapter import ProcessorBBackend
from maxcut.domain.model import MaxCutGraph
from maxcut.io import load_challenge_instance
from maxcut.qaoa.ansatz import build_reduced_qaoa_circuit

g = MaxCutGraph.from_challenge_instance(load_challenge_instance("instances/challenge/o1_maxcut_instance.json"))
bound = build_reduced_qaoa_circuit(g, p=1, fixed_node=0, include_measurements=True).bind(gamma_values=[2.5270], beta_values=[2.6983])

pa = ProcessorABackend(seed_transpiler=42)
pb = ProcessorBBackend(seed_transpiler=42)

_, ma = pa.transpile_circuit(bound, optimization_level=1)
_, mb = pb.transpile_circuit(bound, optimization_level=1)

print("Processor A:")
print("  Physical qubits used:", ma["physical_qubits_used"])
print("  Active count:", ma["physical_qubits_active_count"])
print("  Depth:", ma["transpiled_depth"])
print("  Total gates:", ma["transpiled_total_gates"])
print("  2Q gates:", ma["transpiled_2q_gates"], "Basis:", ma["basis_synthesis_2q_gates"], "Routing:", ma["routing_2q_gates"])
print("  SWAPs:", ma["routing_swap_count"])
print("  Gate breakdown:", ma["gate_breakdown"])

print("\nProcessor B:")
print("  Physical qubits used:", mb["physical_qubits_used"])
print("  Active count:", mb["physical_qubits_active_count"])
print("  Depth:", mb["transpiled_depth"])
print("  Total gates:", mb["transpiled_total_gates"])
print("  2Q gates:", mb["transpiled_2q_gates"], "Basis:", mb["basis_synthesis_2q_gates"], "Routing:", mb["routing_2q_gates"])
print("  SWAPs:", mb["routing_swap_count"])
print("  Gate breakdown:", mb["gate_breakdown"])
