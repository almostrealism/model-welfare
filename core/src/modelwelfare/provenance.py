"""Provenance stamps for machine-produced records."""

import subprocess
from pathlib import Path

from modelwelfare.v1 import common_pb2


def current(host: str) -> common_pb2.Provenance:
    """Provenance for this checkout on the given logical host.

    ``host`` must be a logical host name from the registry in the top-level
    README. ``code_version`` is this repository's git commit, empty when git
    or the repository is unavailable (e.g. an installed wheel). ``created_at``
    is left unset; the producer stamps it per record.
    """
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parent,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = ""
    return common_pb2.Provenance(code_version=commit, host=host)
