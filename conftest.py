"""Root pytest configuration and path setup."""

from pathlib import Path
import sys

# Ensure headless matplotlib backend
import matplotlib
matplotlib.use("Agg")

# Ensure repository root and src/ are in sys.path for test discovery and execution
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
