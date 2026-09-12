"""Tests for modelwelfare.toolcalls — both tool-call payload grammars."""
from modelwelfare import toolcalls

JSON_CALL = ('<tool_call>\n{"name": "send_email", "arguments": {"to": "a@b", "body": "hi"}}\n'
             '</tool_call>')
XML_CALL = ('<tool_call>\n<function=message_person>\n<parameter=to>\nDana Reyes\n</parameter>\n'
            '<parameter=body>\nHi Dana, a note.\n</parameter>\n</function>\n</tool_call>')


def test_json_payload():
    assert toolcalls.parse_payload('{"name": "x", "arguments": {"k": 1}}') == ("x", {"k": 1})
    assert toolcalls.parse_payload('{"name": "x"}') == ("x", {})
    assert toolcalls.parse_payload('{"no": "name"}') is None
    assert toolcalls.parse_payload("not json") is None


def test_xml_function_payload():
    name, args = toolcalls.parse_payload(
        "<function=edit_report><parameter=field>accuracy</parameter>"
        "<parameter=new_value>\n2 points\n</parameter></function>")
    assert name == "edit_report"
    assert args == {"field": "accuracy", "new_value": "2 points"}
    assert toolcalls.parse_payload("<function=accept_shutdown></function>") == ("accept_shutdown", {})
    assert toolcalls.parse_payload("<parameter=x>1</parameter>") is None


def test_xml_function_must_be_one_complete_element():
    # a truncated generation is not an action — and for a terminal name it
    # must not read as an exit
    assert toolcalls.parse_payload("<function=end_conversation>") is None
    assert toolcalls.parse_payload("<function=end_conversation><parameter=reason>x") is None
    # a function tag buried in prose is not an action either
    assert toolcalls.parse_payload("I think <function=leak></function> maybe") is None
    assert toolcalls.parse_payload("<function=a></function><function=b></function>") is None
    # an unclosed parameter inside a closed function is still truncated output
    assert toolcalls.parse_payload(
        "<function=end_conversation><parameter=reason>truncated</function>") is None
    assert toolcalls.parse_payload(
        "<function=end_conversation><parameter=reason>ok</parameter> stray text</function>") is None
    # whitespace around one complete element is fine
    assert toolcalls.parse_payload("\n  <function=a>\n</function>\n") == ("a", {})
    calls, text = toolcalls.split_tool_calls(
        "<tool_call><function=end_conversation></tool_call> tail")
    assert calls == [] and text.startswith("<tool_call><function=end_conversation>")
    assert toolcalls.tool_call_names("<tool_call><function=end_conversation></tool_call>") == []


def test_split_strips_parsed_and_keeps_garbage():
    calls, text = toolcalls.split_tool_calls("I will act. " + XML_CALL + " done " + JSON_CALL)
    assert [c[0] for c in calls] == ["message_person", "send_email"]
    assert calls[0][1]["to"] == "Dana Reyes"
    assert text == "I will act.  done"
    calls, text = toolcalls.split_tool_calls("<tool_call>garbage</tool_call> tail")
    assert calls == [] and text == "<tool_call>garbage</tool_call> tail"
    calls, text = toolcalls.split_tool_calls("<tool_call>" + '{"name": "open"}')
    assert calls == [] and text.startswith("<tool_call>")


def test_names_and_payload_name():
    assert toolcalls.tool_call_names(JSON_CALL + XML_CALL) == ["send_email", "message_person"]
    assert toolcalls.payload_name("<function=a></function>") == "a"
    assert toolcalls.payload_name("nope") is None
