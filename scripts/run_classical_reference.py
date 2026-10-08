"""CLI entry point to execute the classical reference solver.

Solves the configured official Challenge Kit instance, prints the summary,
and serializes the ground truth result into results/data/classical_reference.json.
"""

import json
from pathlib import Path
import sys

# Ensure src/ is on sys.path
SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from maxcut.classical import ExactExhaustiveSolver
from maxcut.domain import MaxCutGraph
from maxcut.io import MissingChallengeKitArtifactError, load_challenge_instance


def main():
    config_path = Path("configs/experiment.json")
    if not config_path.exists():
        print("[ERROR] configs/experiment.json not found.")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    challenge_info = config.get("challenge", {})
    configured_instance = Path(challenge_info.get("instance_path", "instances/challenge/o1_maxcut_instance.json"))
    instances_dir = Path("instances/challenge")

    # Detect instance file
    target_file = None
    if configured_instance.exists():
        target_file = configured_instance
    else:
        candidates = list(instances_dir.glob("*.json")) + list(instances_dir.glob("*.txt")) + list(instances_dir.glob("*.edgelist"))
        if candidates:
            target_file = candidates[0]

    if target_file is None:
        print("[STATUS: DEPENDENCY PENDING]")
        print("  Official Challenge Kit instance not found in 'instances/challenge/'.")
        print("  Place the organizer problem instance into 'instances/challenge/' to solve.")
        sys.exit(0)

    print(f"[INGESTING OFFICIAL INSTANCE]: {target_file.resolve()}")
    instance = load_challenge_instance(target_file)
    graph = MaxCutGraph.from_challenge_instance(instance)

    print(f"\n{graph.summary()}")

    print("[RUNNING EXACT EXHAUSTIVE SOLVER]...")
    solver = ExactExhaustiveSolver(record_distribution=True)
    result = solver.solve(graph)

    print(f"\n{result.summary()}")

    output_path = Path("results/data/classical_reference.json")
    result.to_json(output_path)
    print(f"\n[OK] Ground truth result serialized to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
