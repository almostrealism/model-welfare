"""Unit tests for the fleet host-orchestration CLI.

These test the pure logic — registry resolution, LAN-first target ordering,
endpoint parsing, health-probe interpretation, and remote command assembly —
with the single process-execution seam (fleet._run / run_on) monkeypatched, so
nothing here touches the network.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fleet  # noqa: E402


def write(tmp_path, name, obj):
    path = tmp_path / name
    path.write_text(json.dumps(obj))
    return str(path)


# --- registry --------------------------------------------------------------

def test_default_registry_is_lan_first():
    hosts = fleet.load_hosts("/nonexistent/path.json")
    assert "halo" in hosts
    # The LAN address must precede the WAN name so a flaky WAN is only a fallback.
    assert hosts["halo"].targets[0] == "agent1@10.0.0.127"
    assert hosts["halo"].targets[1] == "agent1@amd-halo"
    assert hosts["studio"].is_local


def test_load_hosts_from_file(tmp_path):
    path = write(tmp_path, "hosts.json", {
        "box": {"targets": ["u@lan", "u@wan"], "repo": "~/r", "aliases": ["b"]},
    })
    hosts = fleet.load_hosts(path)
    assert hosts["box"].targets == ["u@lan", "u@wan"]
    assert hosts["box"].repo == "~/r"
    assert hosts["box"].aliases == ["b"]
    assert not hosts["box"].is_local


def test_resolve_alias_matches_name_and_alias():
    hosts = fleet.load_hosts("/nonexistent")
    assert fleet.resolve_alias(hosts, "halo") == "halo"
    assert fleet.resolve_alias(hosts, "amd-halo") == "halo"
    assert fleet.resolve_alias(hosts, "10.0.0.127") == "halo"
    assert fleet.resolve_alias(hosts, "nope") is None


# --- endpoints -------------------------------------------------------------

def test_load_endpoints_maps_url_host_to_logical(tmp_path):
    path = write(tmp_path, "endpoints.json", {
        "_comment": "ignore me",
        "a": {"kind": "vllm", "url": "http://amd-halo:8011", "model": "m"},
        "b": {"kind": "llamacpp", "url": "http://127.0.0.1:8090"},
        "bad": {"kind": "vllm"},
    })
    hosts = fleet.load_hosts("/nonexistent")
    eps = {e.ident: e for e in fleet.load_endpoints(path, hosts)}
    assert "_comment" not in eps and "bad" not in eps
    assert eps["a"].host == "halo" and eps["a"].port == 8011 and eps["a"].kind == "vllm"
    assert eps["b"].host == "studio" and eps["b"].port == 8090


def test_load_endpoints_missing_file_is_empty():
    assert fleet.load_endpoints("/no/such/file.json", {}) == []


# --- remote command assembly ----------------------------------------------

def test_shell_quote_leaves_simple_tokens_bare():
    assert fleet._shell_quote("rtn-w4") == "rtn-w4"
    assert fleet._shell_quote("services/vllm/ladder.sh") == "services/vllm/ladder.sh"
    assert fleet._shell_quote("a b") == "'a b'"
    assert fleet._shell_quote("it's") == "'it'\\''s'"


def test_ssh_argv_has_connect_timeout_and_batchmode():
    argv = fleet.ssh_argv("u@h", "cd x && ls")
    assert argv[0] == "ssh"
    assert f"ConnectTimeout={fleet.SSH_CONNECT_TIMEOUT}" in argv
    assert "BatchMode=yes" in argv
    assert argv[-2:] == ["u@h", "cd x && ls"]


def test_run_on_local_runs_in_repo_root(monkeypatch):
    captured = {}

    def fake_run(argv, cwd=None, capture_output=None, text=None, timeout=None, check=None):
        captured["argv"] = argv
        captured["cwd"] = cwd
        class R:
            returncode = 0
            stdout = "ok"
            stderr = ""
        return R()

    monkeypatch.setattr(fleet.subprocess, "run", fake_run)
    host = fleet.Host(name="studio", targets=[])
    result = fleet.run_on(host, ["echo", "hi"])
    assert result.returncode == 0
    assert captured["cwd"] == fleet.REPO_ROOT
    assert captured["argv"] == ["echo", "hi"]


def test_run_on_remote_uses_first_reachable_target(monkeypatch):
    # First target refuses (rc!=0), second answers.
    calls = []

    def fake_run(argv, timeout=None):
        calls.append(argv)
        class R:
            pass
        r = R()
        # ssh <opts> <target> <cmd> ; target is second-to-last
        target = argv[-2]
        if target == "u@lan":
            r.returncode = 255  # "true" probe fails => unreachable
            r.stdout = r.stderr = ""
        else:
            r.returncode = 0
            r.stdout = "done"
            r.stderr = ""
        return r

    monkeypatch.setattr(fleet, "_run", fake_run)
    host = fleet.Host(name="box", targets=["u@lan", "u@wan"], repo="~/r")
    result = fleet.run_on(host, ["services/vllm/ladder.sh", "rtn-w4"])
    assert result.returncode == 0
    # The delegated command must be assembled against the reachable (wan) target
    # and run from the host repo.
    final = calls[-1]
    assert final[-2] == "u@wan"
    assert final[-1] == "cd ~/r && services/vllm/ladder.sh rtn-w4"


def test_run_on_remote_returns_none_when_unreachable(monkeypatch):
    monkeypatch.setattr(fleet, "reachable_target", lambda host: None)
    host = fleet.Host(name="box", targets=["u@lan"], repo="~/r")
    assert fleet.run_on(host, ["ls"]) is None


# --- health probe interpretation ------------------------------------------

def test_probe_up_on_200(monkeypatch):
    class R:
        returncode = 0
        stdout = "200 0.031"
        stderr = ""
    monkeypatch.setattr(fleet, "run_on", lambda *a, **k: R())
    health = fleet.probe(fleet.Host("halo", ["u@h"]), 8011)
    assert health["up"] is True and health["code"] == "200"
    assert health["latency"] == pytest.approx(0.031)


def test_probe_down_on_nonzero(monkeypatch):
    class R:
        returncode = 7
        stdout = ""
        stderr = "connection refused"
    monkeypatch.setattr(fleet, "run_on", lambda *a, **k: R())
    health = fleet.probe(fleet.Host("halo", ["u@h"]), 8011)
    assert health["up"] is False and "connection refused" in health["error"]


def test_probe_down_when_host_unreachable(monkeypatch):
    monkeypatch.setattr(fleet, "run_on", lambda *a, **k: None)
    health = fleet.probe(fleet.Host("halo", ["u@h"]), 8011)
    assert health["up"] is False and health["error"] == "host unreachable"


# --- status exit code ------------------------------------------------------

def test_status_returns_nonzero_when_any_endpoint_down(monkeypatch, capsys):
    hosts = fleet.load_hosts("/nonexistent")
    eps = [
        fleet.Endpoint("a", "halo", 8000, "vllm"),
        fleet.Endpoint("b", "halo", 8011, "vllm"),
    ]

    def fake_probe(host, port, *a, **k):
        return {"up": port == 8000, "code": "200" if port == 8000 else "000"}

    monkeypatch.setattr(fleet, "probe", fake_probe)
    rc = fleet.cmd_status(hosts, eps, "all", as_json=True)
    assert rc == 1  # one endpoint down => nonzero
    out = json.loads(capsys.readouterr().out)
    assert {r["endpoint"]: r["up"] for r in out} == {"a": True, "b": False}
