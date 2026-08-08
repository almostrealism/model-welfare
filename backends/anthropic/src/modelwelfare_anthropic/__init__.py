"""Anthropic API backend — used as the reference judge.

Text-only generation for judging tasks; no tool affordances, no activation
capture, no seeding (the API has none). Requests are billed: callers should
track usage against the budget recorded in docs/PLANNING.md.
"""

from modelwelfare_anthropic.client import AnthropicBackend

__all__ = ["AnthropicBackend"]
