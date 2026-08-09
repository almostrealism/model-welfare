#!/usr/bin/env bash
# hostctl — thin SSH wrapper for driving model-serving launchers across the
# fleet from one place. It does not reimplement the launchers; it runs each
# host's own script (services/vllm/ladder.sh, services/llamacpp/rungs.sh)
# over SSH, so there is one source of truth per host.
#
#   hostctl.sh <host> status
#   hostctl.sh <host> <launcher> <args...>
#   hostctl.sh <host> logs <container>
#   hostctl.sh <host> exec <command...>
#
# Hosts are the logical names from the top-level README registry, resolved
# to ssh targets in the table below. Examples:
#   hostctl.sh halo ladder bf16 rtn-w4     # start ladder rungs on halo
#   hostctl.sh halo ladder --status
#   hostctl.sh studio rungs judge-30b      # start a rung on the studio
#   hostctl.sh halo logs mw-ladder-rtn-w4

set -euo pipefail

host_target() {
  case "$1" in
    halo)   echo "agent1@amd-halo" ;;
    studio) echo "" ;;  # local
    *) echo "unknown host: $1 (known: halo, studio)" >&2; exit 2 ;;
  esac
}

# Repo path on each host (this repo may live at a different path per
# machine). Edit for your fleet; the local checkout is derived from this
# script's own location.
host_repo() {
  case "$1" in
    halo)   echo "~/repo/model-welfare" ;;
    studio) (cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd) ;;
  esac
}

run_on() {
  local host="$1"; shift
  local target repo
  target=$(host_target "$host")
  repo=$(host_repo "$host")
  if [ -z "$target" ]; then
    (cd "${repo/#\~/$HOME}" && "$@")
  else
    ssh -o ConnectTimeout=10 "$target" "cd $repo && $(printf '%q ' "$@")"
  fi
}

HOST="${1:?usage: hostctl.sh <host> <verb> [args]}"
VERB="${2:?usage: hostctl.sh <host> <verb> [args]}"
shift 2

case "$VERB" in
  status)  run_on "$HOST" services/vllm/ladder.sh --status ;;
  ladder)  run_on "$HOST" services/vllm/ladder.sh "$@" ;;
  rungs)   run_on "$HOST" services/llamacpp/rungs.sh "$@" ;;
  logs)    run_on "$HOST" podman logs --tail 60 "$1" ;;
  exec)    run_on "$HOST" "$@" ;;
  *) echo "unknown verb: $VERB (status|ladder|rungs|logs|exec)" >&2; exit 2 ;;
esac
