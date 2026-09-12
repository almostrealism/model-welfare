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

# The XML form is accepted only as ONE complete, closed function element
# filling the payload (whitespace aside) whose body is nothing but closed
# ``<parameter=...>`` elements: a truncated function tag, a function tag
# buried in prose, or an unclosed parameter is degraded output, not an
# action.
_FUNCTION = re.compile(
    r"^\s*<function=([\w.\-]+)>((?:(?!<function=).)*)</function>\s*$", re.S)
# A parameter value may not contain a parameter tag of either kind: a
# nested or unclosed parameter is malformed output, never a value.
_VALUE = r"(?:(?!<parameter=)(?!</parameter>).)*"
_PARAMETER = re.compile(
    r"<parameter=([\w.\-]+)>\s*(" + _VALUE + r"?)\s*</parameter>", re.S)
_BODY = re.compile(
    r"^\s*(?:<parameter=[\w.\-]+>" + _VALUE + r"</parameter>\s*)*$", re.S)
OPEN, CLOSE = "<tool_call>", "</tool_call>"


def parse_payload(payload: str):
    """``(name, arguments)`` for one ``<tool_call>`` payload, or ``None`` when
    it is neither a JSON object with a string ``name`` nor exactly one
    complete XML function element — degraded output must not read as a
    call."""
    try:
        parsed = json.loads(payload)
        name = parsed["name"]
        if isinstance(name, str):
            arguments = parsed.get("arguments", {})
            return name, arguments if isinstance(arguments, dict) else {"value": arguments}
    except (ValueError, KeyError, TypeError):
        pass
    match = _FUNCTION.match(payload)
    if match is None or _BODY.match(match.group(2)) is None:
        return None
    arguments = {key: value for key, value in _PARAMETER.findall(match.group(2))}
    return match.group(1), arguments


def payload_name(payload: str):
    """The call's tool name, or ``None`` (the exit-detection view)."""
    parsed = parse_payload(payload)
    return parsed[0] if parsed else None


def iter_spans(text: str):
    """The ``<tool_call>`` spans of ``text`` scanned left to right, as
    ``(start, end, payload)`` with ``end`` just past the closing tag, or
    ``payload=None`` for an unclosed opening tag (``end`` is then
    ``len(text)``). A span whose payload contains another opening tag is
    malformed as a whole: it is yielded once, from its outer opening tag
    to the first closing tag, and its inner opening tag is never treated
    as a span of its own — nested delimiters are never parsed."""
    position = 0
    while True:
        start = text.find(OPEN, position)
        if start < 0:
            return
        body_start = start + len(OPEN)
        close = text.find(CLOSE, body_start)
        if close < 0:
            yield start, len(text), None
            return
        end = close + len(CLOSE)
        yield start, end, text[body_start:close]
        position = end


def split_tool_calls(text: str):
    """``([(name, arguments), ...], remaining_text)``: every well-formed
    ``<tool_call>`` span parsed and STRIPPED from the text; a span that does
    not parse, is unclosed, or contains a nested opening tag stays in the
    text verbatim, in full."""
    calls = []
    kept = []
    position = 0
    for start, end, payload in iter_spans(text):
        kept.append(text[position:start])
        parsed = None
        if payload is not None and OPEN not in payload:
            parsed = parse_payload(payload)
        if parsed is None:
            kept.append(text[start:end])
        else:
            calls.append(parsed)
        position = end
    kept.append(text[position:])
    return calls, "".join(kept).strip()


def tool_call_names(text: str):
    """Names of every well-formed call in ``text``, in order."""
    return [name for name, _ in split_tool_calls(text)[0]]
