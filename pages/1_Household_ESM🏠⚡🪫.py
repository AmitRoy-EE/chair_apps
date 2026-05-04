import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
OEMOF_DIR = ROOT_DIR / "submodules" / "oemof_household"

sys.path.insert(0, str(OEMOF_DIR))

from oemof_app import run

run()
