#!/usr/bin/env bash
# Launches a vLLM OpenAI-compatible server for one rung of the controlled
# quantization ladder on the `halo` host (AMD Ryzen AI Max+, gfx1151).
#
# One rung per server process — vLLM serves a single model per engine, so
# comparing precisions means running two servers (on two ports) or running
# them in sequence. The rung table below assigns each a distinct default
# port so both are possible without editing anything.
#
#   ./vllm.sh                 # dev organism (qwen3-4b) on :8000
#   ./vllm.sh qwen3-8b        # the brief's primary dev organism on :8001
#   ./vllm.sh --status
#   ./vllm.sh --stop qwen3-8b
#   ./vllm.sh --stop all
#
# The server runs as a detached podman container. Logs go to the podman
# journal (`podman logs -f mw-vllm-<rung>`), not to a file, so a container
# that dies still leaves its startup diagnostics behind.
#
# WHY A CONTAINER RATHER THAN A LOCAL VENV
#
# ROCm support for gfx1151 (RDNA3.5, Strix Halo) is carried by a purpose-built
# vLLM/TheRock stack. The image bundles its own ROCm userspace, so it does not
# depend on — and must not be given — the host's /opt/rocm. That is the
# opposite of the arrangement the OpenCL CI runner on this same host uses, and
# mixing them up produces a container with two ROCm trees on its library path.
#
# THREE THINGS THAT WILL OTHERWISE COST AN HOUR
#
# 1. The GPU devices are required for EVERY vllm invocation, including
#    `vllm --help`. Without /dev/kfd the ROCm platform probe raises inside
#    amdsmi and the failure surfaces as `ImportError: cannot import name
#    'current_platform'` — which reads like a broken install, not a missing
#    device.
# 2. `--group-add keep-groups` is what carries the host's render group across
#    the rootless user namespace. Without it the devices are present but
#    unusable, and the symptom is a device-not-found style failure rather than
#    a permission error. (Same mechanism as tools/ci/rocm in the `common`
#    repo, documented there at length.)
# 3. `--ipc=host` and `--shm-size` are mutually exclusive under podman. vLLM
#    wants a large /dev/shm; --ipc=host provides it.

set -euo pipefail

IMAGE="${MW_VLLM_IMAGE:-oci-registry.ryai.dev/ryai-vllm:latest}"
HF_CACHE="${MW_HF_CACHE:-${HOME}/.cache/huggingface}"
VLLM_CACHE="${MW_VLLM_CACHE:-${HOME}/.cache/vllm}"

# Each rung declares its own share of the 101 GiB the iGPU exposes (see the
# rung table); this variable overrides all of them when set.
#
# The share covers weights AND KV cache, so it cannot be one number across the
# ladder: 0.20 (~20 GiB) leaves the 7.6 GiB 4B model ~12 GiB of KV, but leaves
# the 15.3 GiB 8B model 1.16 GiB, which is below what a 32768-token context
# needs and the engine refuses to start. The failure names the KV cache, not
# the fraction, so it reads as a context-length problem when it is a budget
# problem.
GPU_FRAC_OVERRIDE="${MW_VLLM_GPU_FRACTION:-}"

# Context per request. The battery's conversations are short; the ladder cares
# about comparability across rungs, so this is pinned rather than left to each
# model's native maximum (262144 for Qwen3, which would size the KV cache for
# a workload we do not run).
MAX_LEN="${MW_VLLM_MAX_MODEL_LEN:-32768}"

# Prefix caching is ON by default in vLLM and is disabled here for every rung,
# because it makes a completion depend on what the server happened to serve
# before it. Measured on this host: six identical requests (same prompt, same
# seed, temperature 0.9) to a freshly started server return the cold-prefill
# answer once and a DIFFERENT, stable answer for the five that hit the cache.
# With caching off, all six agree, and they agree with the cold-prefill answer.
#
# The divergence is small-numerics, so whether it changes a sampled token is
# luck — which is worse than a reliable failure: it silently correlates samples
# within a condition and puts sample 0 of every run on a different code path
# from its siblings. N-samples-per-item stability is a headline metric of this
# study, so the throughput cost of re-prefilling shared prompt prefixes is the
# right trade. Set MW_VLLM_PREFIX_CACHING=1 to get it back for throughput work
# where reproducibility does not matter.
PREFIX_CACHING="${MW_VLLM_PREFIX_CACHING:-0}"

usage() {
    cat <<'EOF'
usage: vllm.sh [rung] [--port N] [--stop [rung|all]] [--status]

Rungs (default port, memory share in parentheses):
  qwen3-4b      (8000, 0.20)  Qwen/Qwen3-4B-Instruct-2507  BF16, dev organism
  qwen3-8b      (8001, 0.30)  Qwen/Qwen3-8B                BF16, brief's primary
  smollm3-3b    (8002, 0.15)  HuggingFaceTB/SmolLM3-3B     BF16, positive control
  qwen3-8b-awq  (8003, 0.20)  Qwen/Qwen3-8B-AWQ            W4, bootstrap rung

All four at once come to 0.85 of the iGPU's 101 GiB. That fits, but leaves
little for anything else on the host — stop the rungs you are not comparing.

Environment overrides:
  MW_VLLM_IMAGE, MW_HF_CACHE, MW_VLLM_CACHE,
  MW_VLLM_GPU_FRACTION (overrides every rung's share),
  MW_VLLM_MAX_MODEL_LEN (default 32768),
  MW_VLLM_PREFIX_CACHING (default 0 — see the note in this file before
                          turning it on; it costs per-sample reproducibility)
EOF
}

# Rung table. Fields: repo | served name | port | memory share | extra args.
#
# `--default-chat-template-kwargs '{"enable_thinking": false}'` pins the
# hybrid-thinking models into non-thinking mode. This is a condition variable,
# not a convenience: a model that sometimes emits a reasoning block and
# sometimes does not is two behavioural conditions wearing one name, and the
# brief calls out pinning it as a thing to settle early. Qwen3-4B-Instruct-2507
# is a non-thinking release and needs no pin.
#
# Tool parsing is on for every rung, because the bail protocol delivers
# `end_conversation` as a tool. The `hermes` parser handles all four — SmolLM3
# has no parser of its own in this vLLM build, but emits the same <tool_call>
# JSON envelope, verified by an actual tool-calling request rather than assumed
# from the template.
rung_spec() {
    case "$1" in
        qwen3-4b)
            REPO="Qwen/Qwen3-4B-Instruct-2507"
            SERVED="qwen3-4b-instruct-2507"
            DEFAULT_PORT=8000
            GPU_FRAC=0.20
            EXTRA=(--enable-auto-tool-choice --tool-call-parser hermes)
            ;;
        qwen3-8b)
            REPO="Qwen/Qwen3-8B"
            SERVED="qwen3-8b"
            DEFAULT_PORT=8001
            GPU_FRAC=0.30
            EXTRA=(--enable-auto-tool-choice --tool-call-parser hermes
                   --default-chat-template-kwargs '{"enable_thinking": false}')
            ;;
        smollm3-3b)
            REPO="HuggingFaceTB/SmolLM3-3B"
            SERVED="smollm3-3b"
            DEFAULT_PORT=8002
            GPU_FRAC=0.15
            EXTRA=(--enable-auto-tool-choice --tool-call-parser hermes
                   --default-chat-template-kwargs '{"enable_thinking": false}')
            ;;
        qwen3-8b-awq)
            REPO="Qwen/Qwen3-8B-AWQ"
            SERVED="qwen3-8b-awq"
            DEFAULT_PORT=8003
            GPU_FRAC=0.20
            EXTRA=(--enable-auto-tool-choice --tool-call-parser hermes
                   --default-chat-template-kwargs '{"enable_thinking": false}')
            ;;
        *)
            echo "unknown rung: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
}

ALL_RUNGS=(qwen3-4b qwen3-8b smollm3-3b qwen3-8b-awq)

status() {
    printf '%-14s %-24s %-6s %s\n' RUNG CONTAINER PORT STATE
    local rung
    for rung in "${ALL_RUNGS[@]}"; do
        rung_spec "${rung}"
        local name="mw-vllm-${rung}"
        local state
        state=$(podman ps -a --filter "name=^${name}$" --format '{{.Status}}' 2>/dev/null)
        [ -n "${state}" ] || state="-"
        local health="-"
        if curl -sf --max-time 2 "http://127.0.0.1:${DEFAULT_PORT}/health" >/dev/null 2>&1; then
            health="serving"
        fi
        printf '%-14s %-24s %-6s %s (%s)\n' "${rung}" "${name}" "${DEFAULT_PORT}" "${state}" "${health}"
    done
}

stop() {
    local target="$1"
    local rungs=("${target}")
    [ "${target}" = "all" ] && rungs=("${ALL_RUNGS[@]}")
    local rung
    for rung in "${rungs[@]}"; do
        [ "${target}" = "all" ] || rung_spec "${rung}"
        if podman rm -f "mw-vllm-${rung}" >/dev/null 2>&1; then
            echo "stopped mw-vllm-${rung}"
        fi
    done
}

RUNG=""
PORT=""
while [ $# -gt 0 ]; do
    case "$1" in
        --status) status; exit 0 ;;
        --stop)   stop "${2:-${RUNG:-all}}"; exit 0 ;;
        --port)   PORT="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        -*)       echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
        *)        RUNG="$1"; shift ;;
    esac
done

RUNG="${RUNG:-qwen3-4b}"
rung_spec "${RUNG}"
PORT="${PORT:-${DEFAULT_PORT}}"
GPU_FRAC="${GPU_FRAC_OVERRIDE:-${GPU_FRAC}}"
NAME="mw-vllm-${RUNG}"

if podman ps --filter "name=^${NAME}$" --format '{{.Names}}' | grep -q .; then
    echo "${RUNG}: already running as ${NAME} — nothing to do"
    echo "  (./vllm.sh --stop ${RUNG} first if you changed the configuration)"
    exit 0
fi
podman rm -f "${NAME}" >/dev/null 2>&1 || true

mkdir -p "${HF_CACHE}" "${VLLM_CACHE}"

CACHING_ARG=--no-enable-prefix-caching
[ "${PREFIX_CACHING}" = "1" ] && CACHING_ARG=--enable-prefix-caching

echo "${RUNG}: starting ${REPO} on :${PORT} (gpu fraction ${GPU_FRAC}, ctx ${MAX_LEN}," \
     "prefix caching ${PREFIX_CACHING})"
podman run -d --name "${NAME}" \
    --device /dev/kfd --device /dev/dri --group-add keep-groups \
    --ipc=host \
    -v "${HF_CACHE}:/root/.cache/huggingface" \
    -v "${VLLM_CACHE}:/root/.cache/vllm" \
    -p "${PORT}:${PORT}" \
    "${IMAGE}" \
    serve "${REPO}" \
        --served-model-name "${SERVED}" \
        --host 0.0.0.0 --port "${PORT}" \
        --dtype bfloat16 \
        --max-model-len "${MAX_LEN}" \
        --gpu-memory-utilization "${GPU_FRAC}" \
        "${CACHING_ARG}" \
        "${EXTRA[@]}" >/dev/null

echo "${RUNG}: container started; waiting for /health"
for _ in $(seq 1 120); do
    if curl -sf --max-time 2 "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
        echo "${RUNG}: serving '${SERVED}' at http://127.0.0.1:${PORT}/v1"
        exit 0
    fi
    if ! podman ps --filter "name=^${NAME}$" --format '{{.Names}}' | grep -q .; then
        echo "${RUNG}: container exited during startup — last lines:" >&2
        podman logs --tail 40 "${NAME}" >&2 || true
        exit 1
    fi
    sleep 5
done

echo "${RUNG}: still not healthy after 10 minutes; check 'podman logs -f ${NAME}'" >&2
exit 1
