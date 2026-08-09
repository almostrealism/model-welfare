#!/usr/bin/env bash
# hostctl — DEPRECATED thin shim. The durable cross-host control tool is now
# services/fleet.py, which adds LAN-first host resolution, connect timeouts,
# explicit exit codes, and structured (--json) cross-host health status.
# This shim maps the old verbs onto fleet so existing muscle memory keeps
# working; prefer calling `fleet` directly.
#
#   old: hostctl.sh halo ladder rtn-w4     new: fleet serve halo ladder rtn-w4
#   old: hostctl.sh halo status            new: fleet status halo
#   old: hostctl.sh halo logs <container>  new: fleet logs halo <container>
#   old: hostctl.sh halo exec <cmd...>     new: fleet exec halo -- <cmd...>
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FLEET="$HERE/fleet.py"

HOST="${1:?usage: hostctl.sh <host> <verb> [args]}"
VERB="${2:?usage: hostctl.sh <host> <verb> [args]}"
shift 2

case "$VERB" in
  status)  exec python3 "$FLEET" status "$HOST" ;;
  ladder)  exec python3 "$FLEET" serve "$HOST" ladder "$@" ;;
  rungs)   exec python3 "$FLEET" serve "$HOST" rungs "$@" ;;
  logs)    exec python3 "$FLEET" logs "$HOST" "$1" ;;
  exec)    exec python3 "$FLEET" exec "$HOST" -- "$@" ;;
  *) echo "unknown verb: $VERB (status|ladder|rungs|logs|exec) — see fleet.py" >&2; exit 2 ;;
esac
