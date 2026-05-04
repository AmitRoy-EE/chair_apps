import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "submodules" / "oemof_household"))

from oemof_app import run

run()
