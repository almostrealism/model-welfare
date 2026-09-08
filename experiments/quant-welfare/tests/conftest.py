"""Path setup for the quant-welfare test suite, once.

Several test modules import ``modelwelfare`` (core), the experiment drivers
(``run``, ``analyze``), or the bakeoff ``synthetics`` at top level; before
this conftest they passed only when a module that inserted the right paths
happened to be collected first — the same collection-order dependency fixed
in core/tests. The paths belong here.
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
REPO = BASE.parents[1]
for path in (str(REPO / "core" / "src"), str(BASE), str(BASE / "study1" / "bakeoff")):
    if path not in sys.path:
        sys.path.insert(0, path)

