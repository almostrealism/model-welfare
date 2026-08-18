"""Assistant-span computation for teacher-forced capture — backend-agnostic.

Every capture backend (torch hooks today, MLX taps later) must agree on
which tokens constitute each assistant turn; this module is that single
definition. It is deliberately dependency-free and duck-types the
tokenizer, needing only the two operations the huggingface API provides:

- ``apply_chat_template(messages, tools=..., tokenize=False,
  add_generation_prompt=...)`` -> rendered string
- ``tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)``
  -> mapping with ``input_ids`` and ``offset_mapping``

Spans are computed at the *character* level from the rendered strings and
mapped to tokens via the offset mapping. Character-level, not token-level,
because BPE merges across the template/response junction: the rendered
strings are prefix-stable while their token-id lists are not (the assistant
header's trailing newline fuses with the response's first token when
tokenized in context — the failure the 2026-08-17 journal entry records).
String prefix stability is asserted, not assumed.

On the capture workbench (no repository checkout) this file is shipped
beside ``capture.py``, which imports it with a local-file fallback.
"""


def template_messages(messages):
    """Plan messages -> chat-template message dicts.

    Tool-call entries carry ``arguments_json`` strings in the plan (the
    store's own representation); the template wants parsed arguments, so
    they are decoded here — falling back to the raw string if a stored
    call's arguments were not valid JSON.
    """
    import json

    rendered = []
    for message in messages:
        entry = {"role": message["role"], "content": message["content"]}
        if message.get("tool_calls"):
            calls = []
            for call in message["tool_calls"]:
                try:
                    arguments = json.loads(call["arguments_json"])
                except (json.JSONDecodeError, TypeError):
                    arguments = call["arguments_json"]
                calls.append({"type": "function",
                              "function": {"name": call["name"],
                                           "arguments": arguments}})
            entry["tool_calls"] = calls
        rendered.append(entry)
    return rendered


def render_text(tokenizer, messages, tools=None, add_generation_prompt=False):
    return tokenizer.apply_chat_template(
        messages, tools=tools, tokenize=False,
        add_generation_prompt=add_generation_prompt)


def assistant_spans(tokenizer, messages, tools=None):
    """(token_ids, [(message_index, token_start, token_end)]) for every
    assistant turn, via character offsets into the full rendering."""
    full_text = render_text(tokenizer, messages, tools)
    character_spans = []
    for index, message in enumerate(messages):
        if message["role"] != "assistant":
            continue
        prefix = render_text(tokenizer, messages[:index], tools,
                             add_generation_prompt=True)
        complete = render_text(tokenizer, messages[:index + 1], tools)
        if not complete.startswith(prefix) or not full_text.startswith(complete):
            raise ValueError(
                f"chat template rendering is not prefix-stable at message "
                f"{index}; span computation would be invalid")
        if len(complete) <= len(prefix):
            raise ValueError(f"empty assistant span at message {index}")
        character_spans.append((index, len(prefix), len(complete)))

    encoding = tokenizer(full_text, add_special_tokens=False,
                         return_offsets_mapping=True)
    offsets = encoding["offset_mapping"]
    spans = []
    for index, char_start, char_end in character_spans:
        token_indices = [position for position, (start, end) in enumerate(offsets)
                         if start < char_end and end > char_start]
        if not token_indices:
            raise ValueError(f"no tokens overlap assistant span at message {index}")
        spans.append((index, token_indices[0], token_indices[-1] + 1))
    return encoding["input_ids"], spans
