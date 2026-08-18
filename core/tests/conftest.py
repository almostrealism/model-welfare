"""Make ``modelwelfare`` importable for every core test module.

Several test modules import ``modelwelfare`` at top level without their own
path setup; before this conftest they passed only when a module that DID
insert ``core/src`` happened to be collected first — a collection-order
dependency, not a working configuration. The path belongs here, once.
"""
import sys
from pathlib import Path

SRC = str(Path(__file__).resolve().parents[1] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)
