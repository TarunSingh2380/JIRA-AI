"""Thin Anthropic API wrapper with retry + prompt caching.

We cache the system prompt because it's identical across all 6 repo scans in a
batch — Anthropic charges 10% of input price for cache reads, so this is a real
saving on the full-scan and a small one on nightly patches.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import anthropic
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from .config import require_api_key

log = logging.getLogger(__name__)


def _is_retryable(exc: BaseException) -> bool:
    """Retry on transient failures: rate limits, timeouts, connection errors,
    and 5xx server errors. Do NOT retry on 4xx — those mean our request is
    malformed (bad input, oversize payload, auth failure) and retrying would
    just burn tokens.
    """
    if isinstance(exc, (anthropic.RateLimitError, anthropic.APITimeoutError, anthropic.APIConnectionError)):
        return True
    # InternalServerError is a 500. APIStatusError is the parent class; check
    # status_code for the 5xx range to catch 502/503/504 as well.
    if isinstance(exc, anthropic.InternalServerError):
        return True
    if isinstance(exc, anthropic.APIStatusError):
        status = getattr(exc, "status_code", None)
        if status is not None and 500 <= status < 600:
            return True
    return False


@dataclass
class LLMResult:
    text: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    stop_reason: Optional[str] = None

    @property
    def total_input_tokens(self) -> int:
        return self.input_tokens + self.cache_read_tokens + self.cache_creation_tokens


class LLMClient:
    def __init__(self, model: str = "claude-sonnet-4-6", max_tokens: int = 32_000):
        self.model = model
        self.max_tokens = max_tokens
        self.client = anthropic.Anthropic(api_key=require_api_key())

    @retry(
        retry=retry_if_exception(_is_retryable),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        stop=stop_after_attempt(6),
        reraise=True,
        before_sleep=lambda rs: log.warning(
            "retry %d/%d after %s: %s",
            rs.attempt_number, 6,
            type(rs.outcome.exception()).__name__,
            rs.outcome.exception(),
        ),
    )
    def complete(
        self,
        system: str,
        user: str,
        cache_system: bool = True,
        max_tokens: Optional[int] = None,
    ) -> LLMResult:
        """Send a single-turn message via streaming.

        We always stream because the SDK refuses non-streaming requests whose
        estimated runtime exceeds 10 minutes. With our input sizes (300K+ packed
        tokens) and output cap (32K), we routinely cross that threshold. Streaming
        also gives us partial output preservation if something dies mid-response —
        the chunks accumulated so far are still in memory.
        """
        system_blocks = [
            {
                "type": "text",
                "text": system,
                **({"cache_control": {"type": "ephemeral"}} if cache_system else {}),
            }
        ]

        effective_max = max_tokens if max_tokens is not None else self.max_tokens
        log.info(
            "LLM call (streaming): model=%s, system_chars=%d, user_chars=%d, max_tokens=%d",
            self.model, len(system), len(user), effective_max,
        )

        # messages.stream() is a context manager that yields events. .get_final_message()
        # at the end gives us the full assembled message with usage info.
        with self.client.messages.stream(
            model=self.model,
            max_tokens=effective_max,
            system=system_blocks,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            # Drain the event stream. We don't need to do anything with individual
            # events — the SDK assembles them internally. But iterating is what
            # actually advances the stream.
            for _ in stream.text_stream:
                pass
            final = stream.get_final_message()

        text_parts = [b.text for b in final.content if b.type == "text"]
        text = "".join(text_parts)

        usage = final.usage
        return LLMResult(
            text=text,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
            cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
            stop_reason=final.stop_reason,
        )