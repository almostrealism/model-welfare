# Fleet — cross-machine service control

This project runs LLM services across several machines on a private network: a
subject model instrumented on one host, a judge on another, an orchestrator on
the local machine, quantization workbenches elsewhere. Directing that reliably
from one place — start a server with specific flags, wait until it is actually
answering, tear it down, ask "what is up where" — is its own problem, separate
from the experiment code. `services/fleet.py` is the tool for it.

## What fleet is (and is not)

Fleet is the **mechanism** layer for service lifecycle across hosts. It:

- resolves a **logical host name** (`halo`, `studio`, `mini-1`) to a reachable
  SSH target, **LAN address first, WAN/tailnet name as fallback** — so a flaky
  wide-area path is only ever a backup, never the default;
- runs each host's **own launcher scripts** (`services/vllm/ladder.sh`,
  `services/llamacpp/rungs.sh`) over SSH — it does **not** reimplement them;
  there is one source of truth per host;
- probes endpoint **health uniformly** (HTTP `/health` on the host loopback via
  the same SSH path), and reports a single **structured, cross-host status**;
- fails **fast and explicitly** (short connect timeouts, distinct exit codes)
  instead of hanging or silently half-succeeding.

Fleet is **not** a scheduler, a job queue, or an agent runner. It does not
decide *what* should run where or *when* — it only makes *making it so* (and
checking it) reliable and scriptable.

## Why not FlowTree (yet)

FlowTree already orchestrates agent work across dozens of machines and is
trusted for that. But FlowTree's primitives (`Controller`, `NodeGroup`,
`GitManagedJob`, `AgentRunner`) are built for **short-lived, git-tracked,
one-shot agent jobs**. There is no health check, no restart, no long-running
process supervision, and capability/label routing to "the GPU host" is planned
but not built (`common:flowtree/.../MULTIPLATFORM_NODES.md`). Supervising a
persistent vLLM server would mean writing a new `Job` type *and* the routing
layer — a substantial change to a system whose value is that it is stable, and
in a domain (service supervision) its track record does not cover.

So the durable design is a **mechanism/policy split**:

```
   policy / scheduling                mechanism
   ┌───────────────────┐   subprocess ┌─────────────────────────────┐
   │ FlowTree (later)  │ ───────────▶ │ fleet.py                    │
   │ or a human / CLI  │  fleet serve │  registry + SSH + health    │
   └───────────────────┘  --json      └─────────────────────────────┘
                                               │ runs each host's
                                               ▼ own launcher
                                        ladder.sh / rungs.sh
```

Every fleet command is a subprocess with machine-readable (`--json`) output.
That is exactly the interface a future FlowTree `Job` would call via
`ProcessBuilder` — so building fleet now is not a detour around FlowTree, it is
the **on-ramp**: when we adapt FlowTree to manage these services, fleet is the
thing it drives, and FlowTree keeps doing the dispatch it is proven at. Nothing
here is throwaway.

## Usage

```
fleet hosts                          # registry + reachability (which target answers)
fleet status [host|all]              # probe every declared endpoint; nonzero if any down
fleet status --json                  # same, machine-readable (for a policy layer)
fleet serve halo ladder bf16 rtn-w4  # start rungs via halo's own launcher
fleet stop  halo ladder all          # stop them
fleet wait  qwen3-4b-rtn-w4 --timeout 600   # block until an endpoint is healthy
fleet logs  halo mw-ladder-rtn-w4    # tail a container
fleet exec  halo -- df -h            # escape hatch for arbitrary remote commands
```

Configuration:

- **Host registry** — `services/fleet.hosts.json` (or `$MW_HOSTS`). Each host
  lists `targets` (ordered `user@addr`, LAN first; empty = local), a `repo`
  path, and `aliases` (names/addresses that resolve to it, e.g. `amd-halo` and
  `10.0.0.127` both mean `halo`). If the file is absent, a built-in default
  covers `studio` and `halo`.
- **Endpoints** — the active study's `endpoints.json` (or `$MW_ENDPOINTS`).
  Fleet derives each endpoint's host and port from its URL and probes it; the
  same file the experiment runner uses, so status reflects what the run expects.

## Design notes

- **Health is probed through SSH on the host loopback**, not against an exposed
  port, so it works regardless of firewalling and reuses LAN-first resolution.
- **`serve`/`stop`/`logs` delegate** to the host launcher; the launchers already
  wait for readiness on start, so fleet does not duplicate that — `wait` exists
  for the case where you want to block on an endpoint you did not just start.
- **Pure logic is unit-tested** (`services/tests/test_fleet.py`) with the single
  process-execution seam monkeypatched; nothing in the test suite touches the
  network, and it runs in CI across Python 3.11–3.13.
