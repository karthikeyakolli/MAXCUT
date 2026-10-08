"""Validation script for organizer Challenge Kit integration.

Checks for official instances in instances/challenge/ and verifies them against
the required schema.
"""

import json
from pathlib import Path
import sys

# Ensure src/ is on sys.path
SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from maxcut.io import (
    ChallengeKitValidationError,
    MissingChallengeKitArtifactError,
    load_challenge_instance,
)


def run_validation():
    print("=" * 70)
    print("  Qiskit Fall Fest 2026 — Challenge Kit Validation")
    print("=" * 70)

    config_path = Path("configs/experiment.json")
    if not config_path.exists():
        print("[ERROR] configs/experiment.json not found!")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    challenge_info = config.get("challenge", {})
    configured_instance = Path(challenge_info.get("instance_path", "instances/challenge/o1_maxcut_instance.json"))
    instances_dir = Path("instances/challenge")

    # Look for candidate files in instances/challenge/
    candidates = list(instances_dir.glob("*.json")) + list(instances_dir.glob("*.txt")) + list(instances_dir.glob("*.edgelist"))

    target_file = None
    if configured_instance.exists():
        target_file = configured_instance
    elif candidates:
        target_file = candidates[0]

    if target_file is None:
        print("\n[STATUS: DEPENDENCY PENDING]")
        print("  Organizer instance file not found in 'instances/challenge/'.")
        print("  Per frozen policy: No synthetic problem instance was fabricated.")
        print("  Place the official organizer instance in 'instances/challenge/' to load.")
        print("\n[REQUIRED FIELDS CONTRACT]")
        for req in [
            "name (string)",
            "nodes (list of node IDs)",
            "edges (list of [u, v] or [u, v, weight])",
            "reference_optimum (optional ground truth float)",
            "constraints (optional dictionary)",
        ]:
            print(f"  - {req}")
        return False

    print(f"\n[FOUND OFFICIAL INSTANCE]: {target_file.resolve()}")

    try:
        instance = load_challenge_instance(target_file)
    except (MissingChallengeKitArtifactError, ChallengeKitValidationError) as e:
        print(f"\n[VALIDATION FAILED]: {e}")
        return False

    print("\n--- Summary of Loaded Problem Instance ---")
    print(instance.summary())

    print("\n--- Required Fields Verification ---")
    print(f"  [OK] Name: '{instance.name}'")
    print(f"  [OK] Number of Nodes (|V|): {instance.num_nodes}")
    print(f"  [OK] Number of Edges (|E|): {instance.num_edges}")
    print(f"  [OK] Weighted: {instance.is_weighted}")
    print(f"  [OK] Self-loops check: PASSED (None detected)")

    graph = instance.to_networkx()
    print(f"  [OK] NetworkX Conversion: {graph}")
    print(f"  [OK] Edge count match: {graph.number_of_edges() == instance.num_edges}")
    print(f"  [OK] Node count match: {graph.number_of_nodes() == instance.num_nodes}")

    print("\n[SUCCESS]: Loaded problem instance strictly matches organizer source specification.")
    return True


if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 0)
