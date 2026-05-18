"""LLM client implementations and provider selection.

This file defines the shared LLM client interface, provider-backed clients,
a mock client for local dry runs, and the factory that chooses the correct
client based on application settings. The system prompt contains stable
instructions, while the user message contains the ticket JSON.
"""

import json
import logging
from typing import Protocol

from app.config import Settings
from app.exceptions import LLMConfigurationError

log = logging.getLogger(__name__)


class LLMClient(Protocol):
    def complete(self, system_prompt: str, user_message: str) -> str:
        """Return the model output for a system prompt plus user message."""


class OpenAILLMClient:
    def __init__(self, settings: Settings) -> None:
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
            timeout=settings.llm_timeout_seconds,
        )

    def complete(self, system_prompt: str, user_message: str) -> str:
        log.info("OpenAI LLM call: model=%s input_chars=%d", self.settings.llm_model, len(user_message))
        response = self.client.chat.completions.create(
            model=self.settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            temperature=0.1,
        )

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
    def __init__(self, settings: Settings) -> None:
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
            timeout=settings.llm_timeout_seconds,
        )

    def complete(self, system_prompt: str, user_message: str) -> str:
        log.info("Anthropic LLM call: model=%s input_chars=%d", self.settings.llm_model, len(user_message))
        response = self.client.messages.create(
            model=self.settings.llm_model,
            max_tokens=4096,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            temperature=0.1,
        )

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
    def complete(self, system_prompt: str, user_message: str) -> str:
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


def build_llm_client(settings: Settings) -> LLMClient:
    provider = settings.llm_provider.lower().strip()
    log.info("Building LLM client: provider=%s model=%s", provider, settings.llm_model)

    if provider == "openai":
        return OpenAILLMClient(settings)

    if provider == "anthropic":
        return AnthropicLLMClient(settings)

    if provider == "mock":
        log.warning("LLM_PROVIDER=mock — no real LLM calls will be made")
        return MockLLMClient()

    raise LLMConfigurationError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")
