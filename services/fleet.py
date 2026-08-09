#!/usr/bin/env python3
"""fleet — direct model-serving activity across the lab's machines from one place.

fleet is the *mechanism* layer for multi-host LLM orchestration: it resolves a
logical host name to a reachable SSH target (LAN address first, WAN name as
fallback), runs each host's own launcher scripts over SSH, and probes endpoint
health uniformly. It deliberately does NOT reimplement the launchers
(services/vllm/ladder.sh, services/llamacpp/rungs.sh) — there is one source of
truth per host. It adds the things a bare SSH wrapper lacks: a host registry
with LAN-first resolution, connect timeouts and explicit exit codes, and a
single structured (``--json``) cross-host status/health view.

Because every command is a subprocess with machine-readable output, a future
policy/scheduler layer (e.g. FlowTree) can drive fleet without reimplementing
service supervision: FlowTree stays the dispatcher it is proven to be, fleet
owns start/stop/health.

Usage:
    fleet hosts                          list the registry + reachability
    fleet status [host|all]              probe every declared endpoint (health)
    fleet serve <host> <launcher> [a...] start rung(s): launcher in {ladder,rungs}
    fleet stop  <host> <launcher> <rung|all>
    fleet wait  <endpoint-id> [--timeout S]
    fleet logs  <host> <container>
    fleet exec  <host> -- <command...>

Options:
    --json           machine-readable output where supported
    --endpoints PATH endpoints map (default: $MW_ENDPOINTS or the quant-welfare study)
    --hosts PATH     host registry (default: $MW_HOSTS or services/fleet.hosts.json)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_HOSTS = os.path.join(REPO_ROOT, "services", "fleet.hosts.json")
DEFAULT_ENDPOINTS = os.path.join(
    REPO_ROOT, "experiments", "quant-welfare", "endpoints.json"
)

SSH_CONNECT_TIMEOUT = 5  # seconds; keep short so a dead WAN name fails fast
HEALTH_PATH = "/health"  # both vLLM and llama-server expose /health


@dataclass
class Host:
    """A logical machine and how to reach it.

    ``targets`` is an ordered list of ``user@addr`` SSH destinations tried in
    order; the LAN address comes first so a flaky WAN name is only a fallback.
    An empty ``targets`` list means the local machine (run commands directly).
    """

    name: str
    targets: list[str] = field(default_factory=list)
    repo: str = "~/repo/model-welfare"
    aliases: list[str] = field(default_factory=list)

    @property
    def is_local(self) -> bool:
        return not self.targets


def load_hosts(path: str) -> dict[str, Host]:
    """Load the host registry, falling back to a built-in default fleet."""
    if os.path.exists(path):
        with open(path) as fh:
            raw = json.load(fh)
    else:
        raw = _default_registry()
    hosts: dict[str, Host] = {}
    for name, spec in raw.items():
        hosts[name] = Host(
            name=name,
            targets=list(spec.get("targets", [])),
            repo=spec.get("repo", "~/repo/model-welfare"),
            aliases=list(spec.get("aliases", [])),
        )
    return hosts


def _default_registry() -> dict:
    """The lab's fleet as documented in the top-level README host registry.

    LAN addresses lead; the WAN/tailnet name is the fallback. Used when no
    services/fleet.hosts.json is present so fleet works out of the box.
    """
    return {
        "studio": {"targets": [], "aliases": ["studio-m1u", "127.0.0.1", "localhost"]},
        "halo": {
            "targets": ["agent1@10.0.0.127", "agent1@amd-halo"],
            "aliases": ["amd-halo", "10.0.0.127"],
        },
    }


def resolve_alias(hosts: dict[str, Host], token: str) -> Optional[str]:
    """Map a logical name, alias, or url-host to a registry key."""
    if token in hosts:
        return token
    for name, host in hosts.items():
        if token in host.aliases:
            return name
    return None


@dataclass
class Endpoint:
    """One served model: which host, port, and backend kind."""

    ident: str
    host: str  # logical host name (resolved), or raw url-host if unknown
    port: int
    kind: str
    model: Optional[str] = None
    url: str = ""


def load_endpoints(path: str, hosts: dict[str, Host]) -> list[Endpoint]:
    """Parse the endpoints map into Endpoint records keyed to logical hosts."""
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        raw = json.load(fh)
    eps: list[Endpoint] = []
    for ident, spec in raw.items():
        if ident.startswith("_") or not isinstance(spec, dict) or "url" not in spec:
            continue
        parsed = urlparse(spec["url"])
        url_host = parsed.hostname or ""
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        logical = resolve_alias(hosts, url_host) or url_host
        eps.append(
            Endpoint(
                ident=ident,
                host=logical,
                port=port,
                kind=spec.get("kind", "unknown"),
                model=spec.get("model"),
                url=spec["url"],
            )
        )
    return eps


# --- transport -------------------------------------------------------------
# All process execution funnels through _run so tests can monkeypatch a single
# seam and no command bypasses the connect-timeout / error handling.


def _run(argv: list[str], timeout: Optional[int] = None) -> subprocess.CompletedProcess:
    """Run a local command, capturing output. Never raises on nonzero exit."""
    return subprocess.run(
        argv, capture_output=True, text=True, timeout=timeout, check=False
    )


def ssh_argv(target: str, remote_cmd: str) -> list[str]:
    """Build an ssh argv with a short connect timeout and batch mode."""
    return [
        "ssh",
        "-o",
        f"ConnectTimeout={SSH_CONNECT_TIMEOUT}",
        "-o",
        "BatchMode=yes",
        target,
        remote_cmd,
    ]


def reachable_target(host: Host) -> Optional[str]:
    """Return the first SSH target that answers, or None. Local hosts return ''."""
    if host.is_local:
        return ""
    for target in host.targets:
        result = _run(ssh_argv(target, "true"), timeout=SSH_CONNECT_TIMEOUT + 3)
        if result.returncode == 0:
            return target
    return None


def run_on(host: Host, argv: list[str], timeout: Optional[int] = None):
    """Run a command on a host (locally if is_local, else over the first live target).

    ``argv`` is run from the host's repo directory. Returns the
    CompletedProcess, or None if no SSH target was reachable.
    """
    if host.is_local:
        cwd = REPO_ROOT
        return subprocess.run(
            argv, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False
        )
    target = reachable_target(host)
    if target is None:
        return None
    quoted = " ".join(_shell_quote(a) for a in argv)
    remote = f"cd {host.repo} && {quoted}"
    return _run(ssh_argv(target, remote), timeout=timeout)


def _shell_quote(s: str) -> str:
    """Minimal POSIX single-quote quoting for remote command assembly."""
    if s and all(c.isalnum() or c in "-_./=:" for c in s):
        return s
    return "'" + s.replace("'", "'\\''") + "'"


def probe(host: Host, port: int, path: str = HEALTH_PATH, timeout: int = 4) -> dict:
    """Probe an endpoint's health via curl on the host's loopback.

    Probing through the SSH host (rather than an exposed port) works regardless
    of firewalling and reuses the LAN-first target resolution. Returns a dict
    with ``up`` (bool) and, when reachable, the http ``code`` and ``latency``.
    """
    curl = [
        "curl",
        "-sf",
        "--max-time",
        str(timeout),
        "-o",
        "/dev/null",
        "-w",
        "%{http_code} %{time_total}",
        f"http://127.0.0.1:{port}{path}",
    ]
    result = run_on(host, curl, timeout=timeout + SSH_CONNECT_TIMEOUT + 3)
    if result is None:
        return {"up": False, "error": "host unreachable"}
    if result.returncode != 0:
        return {"up": False, "error": (result.stderr or "no response").strip()[:120]}
    parts = result.stdout.strip().split()
    code = parts[0] if parts else "?"
    latency = float(parts[1]) if len(parts) > 1 else None
    return {"up": code == "200", "code": code, "latency": latency}


# --- commands --------------------------------------------------------------

LAUNCHERS = {
    "ladder": "services/vllm/ladder.sh",
    "rungs": "services/llamacpp/rungs.sh",
}


def cmd_hosts(hosts: dict[str, Host], as_json: bool) -> int:
    rows = []
    for name, host in hosts.items():
        target = "" if host.is_local else (reachable_target(host) or None)
        rows.append(
            {
                "host": name,
                "local": host.is_local,
                "reachable": host.is_local or target is not None,
                "via": target if target else ("local" if host.is_local else None),
                "targets": host.targets,
            }
        )
    if as_json:
        print(json.dumps(rows, indent=2))
    else:
        print(f"{'HOST':<10} {'REACHABLE':<10} VIA")
        for r in rows:
            via = r["via"] or "-"
            print(f"{r['host']:<10} {str(r['reachable']):<10} {via}")
    return 0


def cmd_status(
    hosts: dict[str, Host], endpoints: list[Endpoint], which: str, as_json: bool
) -> int:
    target_host = None
    if which and which != "all":
        target_host = resolve_alias(hosts, which)
        if target_host is None:
            print(f"unknown host: {which}", file=sys.stderr)
            return 2
    rows = []
    for ep in endpoints:
        if target_host and ep.host != target_host:
            continue
        host = hosts.get(ep.host)
        if host is None:
            rows.append({"endpoint": ep.ident, "host": ep.host, "up": False,
                         "error": "host not in registry", "port": ep.port,
                         "kind": ep.kind})
            continue
        health = probe(host, ep.port)
        rows.append(
            {
                "endpoint": ep.ident,
                "host": ep.host,
                "port": ep.port,
                "kind": ep.kind,
                **health,
            }
        )
    if as_json:
        print(json.dumps(rows, indent=2))
    else:
        print(f"{'ENDPOINT':<22} {'HOST':<8} {'PORT':<6} {'UP':<5} DETAIL")
        for r in rows:
            detail = r.get("error") or (
                f"{r.get('code','')} {r.get('latency','')}s".strip()
            )
            print(
                f"{r['endpoint']:<22} {r['host']:<8} {r['port']:<6} "
                f"{str(r.get('up', False)):<5} {detail}"
            )
    any_down = any(not r.get("up", False) for r in rows)
    return 1 if any_down else 0


def cmd_serve(hosts: dict[str, Host], host_name: str, launcher: str, args: list[str]) -> int:
    return _delegate(hosts, host_name, launcher, args)


def cmd_stop(hosts: dict[str, Host], host_name: str, launcher: str, rung: str) -> int:
    return _delegate(hosts, host_name, launcher, ["--stop", rung])


def _delegate(hosts: dict[str, Host], host_name: str, launcher: str, args: list[str]) -> int:
    name = resolve_alias(hosts, host_name)
    if name is None:
        print(f"unknown host: {host_name}", file=sys.stderr)
        return 2
    if launcher not in LAUNCHERS:
        print(f"unknown launcher: {launcher} (known: {', '.join(LAUNCHERS)})",
              file=sys.stderr)
        return 2
    argv = [LAUNCHERS[launcher], *args]
    result = run_on(hosts[name], argv, timeout=900)
    if result is None:
        print(f"{name}: no reachable SSH target", file=sys.stderr)
        return 4
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    return result.returncode


def cmd_wait(
    hosts: dict[str, Host], endpoints: list[Endpoint], ident: str, timeout: int
) -> int:
    ep = next((e for e in endpoints if e.ident == ident), None)
    if ep is None:
        print(f"unknown endpoint: {ident}", file=sys.stderr)
        return 2
    host = hosts.get(ep.host)
    if host is None:
        print(f"endpoint {ident} host {ep.host} not in registry", file=sys.stderr)
        return 2
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        health = probe(host, ep.port)
        if health.get("up"):
            print(f"{ident}: up ({health.get('latency')}s)")
            return 0
        time.sleep(3)
    print(f"{ident}: not healthy after {timeout}s", file=sys.stderr)
    return 1


def cmd_logs(hosts: dict[str, Host], host_name: str, container: str) -> int:
    name = resolve_alias(hosts, host_name)
    if name is None:
        print(f"unknown host: {host_name}", file=sys.stderr)
        return 2
    result = run_on(hosts[name], ["podman", "logs", "--tail", "80", container], timeout=30)
    if result is None:
        print(f"{name}: no reachable SSH target", file=sys.stderr)
        return 4
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    return result.returncode


def cmd_exec(hosts: dict[str, Host], host_name: str, command: list[str]) -> int:
    name = resolve_alias(hosts, host_name)
    if name is None:
        print(f"unknown host: {host_name}", file=sys.stderr)
        return 2
    result = run_on(hosts[name], command, timeout=120)
    if result is None:
        print(f"{name}: no reachable SSH target", file=sys.stderr)
        return 4
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    return result.returncode


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="fleet", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--hosts", default=os.environ.get("MW_HOSTS", DEFAULT_HOSTS))
    p.add_argument("--endpoints",
                   default=os.environ.get("MW_ENDPOINTS", DEFAULT_ENDPOINTS))
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("hosts", help="list the registry + reachability")

    sp = sub.add_parser("status", help="probe declared endpoints")
    sp.add_argument("host", nargs="?", default="all")

    sp = sub.add_parser("serve", help="start rung(s) via a host launcher")
    sp.add_argument("host")
    sp.add_argument("launcher", choices=sorted(LAUNCHERS))
    sp.add_argument("args", nargs=argparse.REMAINDER)

    sp = sub.add_parser("stop", help="stop rung(s) via a host launcher")
    sp.add_argument("host")
    sp.add_argument("launcher", choices=sorted(LAUNCHERS))
    sp.add_argument("rung", nargs="?", default="all")

    sp = sub.add_parser("wait", help="poll an endpoint until healthy")
    sp.add_argument("endpoint")
    sp.add_argument("--timeout", type=int, default=600)

    sp = sub.add_parser("logs", help="tail a container's logs")
    sp.add_argument("host")
    sp.add_argument("container")

    sp = sub.add_parser("exec", help="run an arbitrary command on a host")
    sp.add_argument("host")
    sp.add_argument("command", nargs=argparse.REMAINDER)
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    hosts = load_hosts(args.hosts)
    endpoints = load_endpoints(args.endpoints, hosts)

    if args.cmd == "hosts":
        return cmd_hosts(hosts, args.json)
    if args.cmd == "status":
        return cmd_status(hosts, endpoints, args.host, args.json)
    if args.cmd == "serve":
        extra = args.args[1:] if args.args and args.args[0] == "--" else args.args
        return cmd_serve(hosts, args.host, args.launcher, extra)
    if args.cmd == "stop":
        return cmd_stop(hosts, args.host, args.launcher, args.rung)
    if args.cmd == "wait":
        return cmd_wait(hosts, endpoints, args.endpoint, args.timeout)
    if args.cmd == "logs":
        return cmd_logs(hosts, args.host, args.container)
    if args.cmd == "exec":
        cmd = args.command[1:] if args.command and args.command[0] == "--" else args.command
        return cmd_exec(hosts, args.host, cmd)
    return 2


if __name__ == "__main__":
    sys.exit(main())
