"""Phase F — Anthropic native tool-use investigation loop (read-only).

Seeds Claude with the extracted signals + RRF candidate set and the seven
read-only tools, then runs the messages API tool-use loop until the model stops
or a hard cap (iterations / tokens) is hit. Every tool call and observation is
recorded to an `agent_trace` for audit. The loop never writes code, never runs
code, and never applies changes — its only effect is reading the codebase.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from app.config import Settings
from app.rca.tools import TOOL_SCHEMAS, ToolContext

log = logging.getLogger(__name__)

_SYSTEM = """\
You are a senior engineer performing READ-ONLY root cause analysis of a production
defect. Investigate the codebase using the provided tools to pinpoint the most
likely root cause to a specific repo/file/symbol/lines, and gather the evidence
that proves it.

You may ONLY read. You must not propose applying changes, must not run code, and
must not invent file paths or line numbers — verify everything with a tool.

Method:
- Start from the seeded candidates and extracted error signals.
- Use grep_codebase / read_file to confirm where the faulty logic lives.
- Use find_references and git_blame/git_log to trace how the code is reached and
  when/why it changed.
- Use search_similar_tickets / semantic_code_search to corroborate.
- Stop as soon as you can name the cause with evidence; do not over-explore.

When you are confident (or have exhausted useful leads), STOP CALLING TOOLS and
reply with a short plain-text investigation summary: the suspected root-cause
location, the causal chain, and the key evidence. A separate step will format the
final diagnosis — you only need the findings, not a template.
"""


@dataclass
class AgentResult:
    summary: str
    agent_trace: list[dict[str, Any]] = field(default_factory=list)
    iterations: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    stop_reason: str = ""


def _seed_message(extracted: dict[str, Any], candidates: list[dict[str, Any]],
                  ticket_summary: str) -> str:
    return (
        "DEFECT TICKET\n"
        f"summary: {ticket_summary}\n\n"
        "EXTRACTED SIGNALS\n"
        f"{json.dumps(extracted, indent=2)}\n\n"
        "SEEDED CANDIDATE LOCATIONS (from hybrid retrieval, most likely first)\n"
        f"{json.dumps(candidates, indent=2)}\n\n"
        "Investigate and find the root cause. Use the tools; verify before you conclude."
    )


def run_investigation(
    settings: Settings,
    *,
    ticket_summary: str,
    extracted: dict[str, Any],
    candidates: list[dict[str, Any]],
    allowed_repos: list[str],
    on_event: Optional[Callable[[dict[str, Any]], None]] = None,
    client: Any = None,
    tool_context: Any = None,
) -> AgentResult:
    """Run the read-only tool-use loop. Returns the findings + full agent_trace.

    `client` (Anthropic-like, exposes messages.create) and `tool_context` may be
    injected for tests; otherwise they are built from settings.
    """
    if client is None:
        try:
            from anthropic import Anthropic
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("anthropic package required for RCA agent") from exc
        client = Anthropic(api_key=settings.anthropic_api_key,
                           timeout=settings.llm_timeout_seconds)
    ctx = tool_context if tool_context is not None else ToolContext(settings, allowed_repos)

    messages: list[dict[str, Any]] = [
        {"role": "user", "content": _seed_message(extracted, candidates, ticket_summary)}
    ]
    trace: list[dict[str, Any]] = []
    result = AgentResult(summary="", agent_trace=trace)

    for iteration in range(settings.rca_agent_max_iterations):
        result.iterations = iteration + 1
        if result.input_tokens + result.output_tokens > settings.rca_agent_max_tokens:
            result.stop_reason = "token_cap"
            log.warning("RCA agent hit token cap at iteration %d", iteration + 1)
            break

        resp = client.messages.create(
            model=settings.rca_agent_model,
            max_tokens=4096,
            system=_SYSTEM,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )
        usage = getattr(resp, "usage", None)
        if usage:
            result.input_tokens += getattr(usage, "input_tokens", 0) or 0
            result.output_tokens += getattr(usage, "output_tokens", 0) or 0

        # collect assistant text + any tool calls
        assistant_content: list[dict[str, Any]] = []
        tool_uses: list[Any] = []
        text_parts: list[str] = []
        for block in resp.content:
            btype = getattr(block, "type", None)
            if btype == "text":
                text_parts.append(block.text)
                assistant_content.append({"type": "text", "text": block.text})
            elif btype == "tool_use":
                tool_uses.append(block)
                assistant_content.append({
                    "type": "tool_use", "id": block.id,
                    "name": block.name, "input": block.input,
                })
        messages.append({"role": "assistant", "content": assistant_content})

        if resp.stop_reason != "tool_use" or not tool_uses:
            result.summary = "\n".join(text_parts).strip()
            result.stop_reason = resp.stop_reason or "end_turn"
            break

        # execute each requested tool and feed results back
        tool_results: list[dict[str, Any]] = []
        for tu in tool_uses:
            observation = ctx.dispatch(tu.name, tu.input or {})
            entry = {
                "iteration": iteration + 1,
                "tool": tu.name,
                "input": tu.input,
                "observation": observation,
            }
            trace.append(entry)
            if on_event:
                try:
                    on_event(entry)
                except Exception:  # event sink must never break the loop
                    pass
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": json.dumps(observation)[:12000],
            })
        messages.append({"role": "user", "content": tool_results})
    else:
        result.stop_reason = result.stop_reason or "iteration_cap"

    log.info("RCA agent done: iters=%d tools=%d stop=%s tokens=%d/%d",
             result.iterations, len(trace), result.stop_reason,
             result.input_tokens, result.output_tokens)
    return result
