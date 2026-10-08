"""Circuit visualization utilities for QAOA Max-Cut circuits."""

from pathlib import Path
from typing import Optional, Union

import matplotlib.pyplot as plt

from maxcut.qaoa.ansatz import QAOAAnsatz


def plot_qaoa_circuit(
    ansatz: QAOAAnsatz,
    save_path: Optional[Union[str, Path]] = None,
    output: str = "mpl",
) -> Optional[plt.Figure]:
    """Draws and optionally exports the QAOA QuantumCircuit.

    Args:
        ansatz: QAOAAnsatz instance.
        save_path: Optional destination to save image (e.g. PNG/PDF).
        output: 'mpl' for Matplotlib, 'text' for terminal ASCII.

    Returns:
        Optional[plt.Figure]: Figure if output='mpl', else None.
    """
    if output == "mpl":
        fig = ansatz.circuit.draw(output="mpl")
        if save_path is not None:
            out_file = Path(save_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(out_file, bbox_inches="tight")
        return fig
    else:
        text_art = ansatz.draw_ascii()
        if save_path is not None:
            out_file = Path(save_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(text_art)
        return None
