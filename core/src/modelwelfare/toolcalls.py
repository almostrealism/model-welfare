"""Tool-call payloads in generated assistant text.

The subjects emit tool calls inline as ``<tool_call> ... </tool_call>``
spans, but the payload grammar differs by model family: the Qwen3 line
writes a JSON object (``{"name": ..., "arguments": {...}}``), the
Qwen3.5/3.6 line writes an XML-ish function form
(``<function=NAME><parameter=KEY>VALUE</parameter>...</function>``).
Every consumer that reads a call out of text — ingestion into the store,
exit detection in the steering script — must accept both, or a subject
family silently reads as "never acted". This module is the one place the
grammar lives; the steering script mirrors :func:`payload_name` at its
ship-beside boundary.
"""

import json
import re

_FUNCTION = re.compile(r"<function=([\w.\-]+)>")
_PARAMETER = re.compile(r"<parameter=([\w.\-]+)>\s*(.*?)\s*</parameter>", re.S)


def parse_payload(payload: str):
    """``(name, arguments)`` for one ``<tool_call>`` payload, or ``None`` when
    it is neither a JSON object with a string ``name`` nor an XML function
    form — degraded output must not read as a call."""
    try:
        parsed = json.loads(payload)
        name = parsed["name"]
        if isinstance(name, str):
            arguments = parsed.get("arguments", {})
            return name, arguments if isinstance(arguments, dict) else {"value": arguments}
    except (ValueError, KeyError, TypeError):
        pass
    match = _FUNCTION.search(payload)
    if match is None:
        return None
    arguments = {key: value for key, value in _PARAMETER.findall(payload)}
    return match.group(1), arguments


def payload_name(payload: str):
    """The call's tool name, or ``None`` (the exit-detection view)."""
    parsed = parse_payload(payload)
    return parsed[0] if parsed else None


def split_tool_calls(text: str):
    """``([(name, arguments), ...], remaining_text)``: every well-formed
    ``<tool_call>`` span parsed and STRIPPED from the text; a span that does
    not parse, or is unclosed, stays in the text verbatim."""
    calls = []
    kept = []
    pieces = text.split("<tool_call>")
    kept.append(pieces[0])
    for segment in pieces[1:]:
        payload, closed, rest = segment.partition("</tool_call>")
        parsed = parse_payload(payload) if closed else None
        if parsed is None:
            kept.append("<tool_call>" + segment)
        else:
            calls.append(parsed)
            kept.append(rest)
    return calls, "".join(kept).strip()


def tool_call_names(text: str):
    """Names of every well-formed call in ``text``, in order."""
    return [name for name, _ in split_tool_calls(text)[0]]
