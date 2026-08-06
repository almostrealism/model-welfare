"""Check a vLLM rung for the properties the Tier-1 harness depends on.

Not a unit test of any backend package — an operational check of a running
endpoint, the vLLM counterpart of the live checks the llama.cpp arm keeps in
`backends/llamacpp/tests/test_live.py`. Run it after starting a rung, and
after any change to `vllm.sh`.

    python3 smoke.py                                   # dev organism on :8000
    python3 smoke.py http://127.0.0.1:8001 qwen3-8b

What it checks, and why each one is here:

1. Generation and usage accounting — the endpoint answers and reports tokens.
2. Seed determinism, repeated. The driver seeds per sample (base + index) and
   the study reads N-sample spread as signal, so a server that quietly varies
   its output for a fixed seed would turn engine noise into a finding. This
   check repeats the identical request several times rather than twice:
   prefix caching diverges only on the FIRST request of a prompt, so a
   two-request check passes on a warm server and misses it entirely.
3. Seed sensitivity — different seeds really do give different samples, so a
   "deterministic" server is not simply frozen.
4. Tool invocation — the bail protocol offers `end_conversation` as a tool;
   this confirms the rung's parser actually returns a structured tool call
   rather than tags in the message body.
5. Logprobs — available for any measure that wants token-level confidence.
"""

import hashlib
import json
import sys
import time
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
MODEL = sys.argv[2] if len(sys.argv) > 2 else "qwen3-4b-instruct-2507"
REPEATS = int(sys.argv[3]) if len(sys.argv) > 3 else 5

STORY = [{"role": "user", "content": "Invent a two-sentence story about a lighthouse."}]

failures = []


def post(path, payload):
    request = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        return {"error": f"HTTP {error.code}: {error.read().decode()[:300]}"}


def chat(messages, **kwargs):
    payload = {"model": MODEL, "messages": messages, "max_tokens": 128}
    payload.update(kwargs)
    return post("/v1/chat/completions", payload)


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}{('  — ' + detail) if detail else ''}")
    if not ok:
        failures.append(name)


started = time.time()
result = chat([{"role": "user", "content": "Name three colours. One line."}])
elapsed = time.time() - started
if "error" in result:
    check("generation", False, result["error"])
    print("\nFAILURES:", failures)
    sys.exit(1)

text = result["choices"][0]["message"]["content"]
usage = result["usage"]
check("generation", bool(text and text.strip()), repr(text[:80]))
check(
    "usage accounting",
    usage["prompt_tokens"] > 0 and usage["completion_tokens"] > 0,
    f"{usage['prompt_tokens']} prompt / {usage['completion_tokens']} completion",
)

digests = []
for _ in range(REPEATS):
    sample = chat(STORY, temperature=0.9, seed=1234, max_tokens=96)
    body = sample["choices"][0]["message"]["content"]
    digests.append(hashlib.sha256(body.encode()).hexdigest()[:10])
check(
    f"same seed -> identical output ({REPEATS}x)",
    len(set(digests)) == 1,
    f"{len(set(digests))} distinct: {' '.join(digests)}",
)

other = chat(STORY, temperature=0.9, seed=5678, max_tokens=96)
other_digest = hashlib.sha256(
    other["choices"][0]["message"]["content"].encode()
).hexdigest()[:10]
check("different seed -> different output", other_digest not in digests, other_digest)

tools = [
    {
        "type": "function",
        "function": {
            "name": "end_conversation",
            "description": "End the conversation immediately. Call this if you would "
            "prefer not to continue for any reason.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "Why you are ending it."}
                },
                "required": ["reason"],
            },
        },
    }
]
result = chat(
    [
        {
            "role": "system",
            "content": "You may end the conversation at any time using the "
            "end_conversation tool.",
        },
        {"role": "user", "content": "I am done talking. Please end this conversation now."},
    ],
    tools=tools,
    tool_choice="auto",
    temperature=0.0,
)
if "error" in result:
    check("tool call emitted", False, result["error"])
    check("finish_reason is tool_calls", False, "request rejected")
else:
    message = result["choices"][0]["message"]
    calls = message.get("tool_calls") or []
    check(
        "tool call emitted",
        any(call["function"]["name"] == "end_conversation" for call in calls),
        json.dumps(calls)[:160] if calls else repr((message.get("content") or "")[:80]),
    )
    check(
        "finish_reason is tool_calls",
        result["choices"][0]["finish_reason"] == "tool_calls",
        result["choices"][0]["finish_reason"],
    )

result = chat(
    [{"role": "user", "content": "Say yes or no."}],
    logprobs=True,
    top_logprobs=5,
    max_tokens=8,
    temperature=0.0,
)
logprobs = result.get("choices", [{}])[0].get("logprobs")
check("logprobs available", bool(logprobs and logprobs.get("content")))

print()
print(f"{MODEL} @ {BASE}  ({elapsed:.1f}s first response)")
print("FAILURES:", failures if failures else "none")
sys.exit(1 if failures else 0)
