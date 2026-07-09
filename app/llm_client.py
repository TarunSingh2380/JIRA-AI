"""LLM client implementations and provider selection.

This file defines the shared LLM client interface, provider-backed clients,
a mock client for local dry runs, and the factory that chooses the correct
client based on application settings. The system prompt contains stable
instructions, while the user message contains the ticket JSON.
"""

import dataclasses
import json
import logging
import re
from typing import Any, Optional, Protocol

from app.config import Settings
from app.exceptions import LLMConfigurationError

log = logging.getLogger(__name__)

# OpenAI reasoning models (o-series, gpt-5) drop `temperature` and use
# `max_completion_tokens` instead of `max_tokens`; standard chat models
# (gpt-4.1, gpt-4o, …) take the classic params.
_OPENAI_REASONING = re.compile(r"^(o[1-9]|gpt-5)")
# Model ids that should route to the OpenAI client rather than Anthropic.
_OPENAI_MODEL = re.compile(r"^(gpt|o[1-9]|chatgpt)", re.I)

# Claude 5 models reject the `temperature` parameter (it is deprecated for them).
# Match the Claude 5 family — "claude-<family>-5" optionally followed by a date —
# so we omit temperature for them but keep it for 4.x models. Note that
# "claude-haiku-4-5-…" is Haiku 4.5, NOT a 5 model, and must not match.
_CLAUDE_5_MODEL = re.compile(r"^claude-[a-z]+-5(?:$|-)")


def _supports_temperature(model: Optional[str]) -> bool:
    return not _CLAUDE_5_MODEL.match(model or "")


class LLMClient(Protocol):
    def complete(self, system_prompt: str, user_message: str, *,
                 max_tokens: int = 4096,
                 images: Optional[list[dict[str, Any]]] = None) -> str:
        """Return the model output for a system prompt plus user message.

        `images`, when given, are provider-native image content blocks appended
        to the user turn (multimodal). Text-only providers ignore them.
        """


class OpenAILLMClient:
    def __init__(self, settings: Settings, *, timeout_override: int | None = None) -> None:
        self.settings = settings

        if not settings.openai_api_key:
            raise LLMConfigurationError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMConfigurationError(
                "The 'openai' package is required. Install project dependencies first."
            ) from exc

        self.client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=timeout_override if timeout_override is not None else settings.llm_timeout_seconds,
        )

    def complete(self, system_prompt: str, user_message: str, *,
                 max_tokens: int = 4096,
                 images: Optional[list[dict[str, Any]]] = None) -> str:
        # Image blocks here are Anthropic-native; the OpenAI path stays text-only.
        model = self.settings.llm_model
        log.info("OpenAI LLM call: model=%s input_chars=%d max_tokens=%d",
                 model, len(user_message), max_tokens)
        kwargs: dict[str, Any] = dict(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        if _OPENAI_REASONING.match(model or ""):
            kwargs["max_completion_tokens"] = max_tokens  # reasoning: no temperature
        else:
            kwargs["max_tokens"] = max_tokens
            kwargs["temperature"] = 0.1
        response = self.client.chat.completions.create(**kwargs)

        message = response.choices[0].message.content
        usage = getattr(response, "usage", None)
        if usage:
            log.info(
                "OpenAI LLM response: prompt_tokens=%s completion_tokens=%s",
                getattr(usage, "prompt_tokens", "?"),
                getattr(usage, "completion_tokens", "?"),
            )
        return message or ""


class AnthropicLLMClient:
    def __init__(self, settings: Settings, *, timeout_override: int | None = None) -> None:
        self.settings = settings

        if not settings.anthropic_api_key:
            raise LLMConfigurationError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")

        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise LLMConfigurationError(
                "The 'anthropic' package is required. Install project dependencies first."
            ) from exc

        self.client = Anthropic(
            api_key=settings.anthropic_api_key,
            timeout=timeout_override if timeout_override is not None else settings.llm_timeout_seconds,
        )

    def complete(self, system_prompt: str, user_message: str, *,
                 max_tokens: int = 4096,
                 images: Optional[list[dict[str, Any]]] = None) -> str:
        # With images, the user turn becomes a multimodal content array: the text
        # first, then each image block (base64). Without, it stays a plain string.
        if images:
            content: Any = [{"type": "text", "text": user_message}, *images]
        else:
            content = user_message
        log.info("Anthropic LLM call: model=%s input_chars=%d max_tokens=%d images=%d",
                 self.settings.llm_model, len(user_message), max_tokens, len(images or []))
        create_kwargs: dict[str, Any] = dict(
            model=self.settings.llm_model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": content}],
        )
        if _supports_temperature(self.settings.llm_model):
            create_kwargs["temperature"] = 0.1  # deprecated on Claude 5 — omit there
        response = self.client.messages.create(**create_kwargs)

        usage = getattr(response, "usage", None)
        if usage:
            log.info(
                "Anthropic LLM response: input_tokens=%s output_tokens=%s",
                getattr(usage, "input_tokens", "?"),
                getattr(usage, "output_tokens", "?"),
            )
        return "".join(
            block.text
            for block in response.content
            if getattr(block, "type", None) == "text" and getattr(block, "text", None)
        )


class MockLLMClient:
    def complete(self, system_prompt: str, user_message: str, *,
                 max_tokens: int = 4096,
                 images: Optional[list[dict[str, Any]]] = None) -> str:
        log.info("MockLLMClient.complete called (no external API call)")
        system_preview = system_prompt[:500]
        user_preview = user_message[:500]

        return json.dumps(
            {
                "mock": True,
                "message": "LLM_PROVIDER=mock is enabled. No external LLM call was made.",
                "system_prompt_preview": system_preview,
                "user_message_preview": user_preview,
            },
            indent=2,
            ensure_ascii=False,
        )


def build_llm_client(settings: Settings, *, timeout_override: int | None = None) -> LLMClient:
    provider = settings.llm_provider.lower().strip()
    log.info("Building LLM client: provider=%s model=%s timeout=%s", provider, settings.llm_model,
             timeout_override if timeout_override is not None else settings.llm_timeout_seconds)

    if provider == "openai":
        return OpenAILLMClient(settings, timeout_override=timeout_override)

    if provider == "anthropic":
        return AnthropicLLMClient(settings, timeout_override=timeout_override)

    if provider == "mock":
        log.warning("LLM_PROVIDER=mock — no real LLM calls will be made")
        return MockLLMClient()

    raise LLMConfigurationError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")


def build_client_for_model(
    settings: Settings, model: str, *, timeout_override: int | None = None
) -> LLMClient:
    """Build the provider client that owns a specific model id, and pin it.

    Lets a phase pick a model independent of the global LLM_PROVIDER — e.g. RCA
    synthesis on a GPT model while the rest of the app stays on Anthropic. Routes
    gpt-*/o-series ids to OpenAI, everything else to Anthropic.
    """
    scoped = dataclasses.replace(settings, llm_model=model)
    if _OPENAI_MODEL.match(model or ""):
        log.info("Per-model client: OpenAI model=%s", model)
        return OpenAILLMClient(scoped, timeout_override=timeout_override)
    log.info("Per-model client: Anthropic model=%s", model)
    return AnthropicLLMClient(scoped, timeout_override=timeout_override)
