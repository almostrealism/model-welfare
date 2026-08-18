"""Path setup for every backend's tests, once.

Before this conftest the backend suites were runnable only under CI's
explicit PYTHONPATH — locally they failed collection, the same
collection-order/path fragility fixed in core/tests and the experiment
tests. Each backend's src plus core/src goes on the path here, so
``pytest backends`` behaves identically on a laptop and in CI.
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
REPO = BASE.parent
paths = [str(REPO / "core" / "src")]
paths += [str(entry / "src") for entry in sorted(BASE.iterdir())
          if (entry / "src").is_dir()]
for path in paths:
    if path not in sys.path:
        sys.path.insert(0, path)
