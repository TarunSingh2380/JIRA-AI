"""Ollama embedding client.

Uses Ollama's /api/embed endpoint (batch-capable) to generate dense vector
embeddings for whatever model is configured via OLLAMA_EMBED_MODEL.

Usage:
    embedder = OllamaEmbedder(base_url, model)
    if embedder.is_available():
        vectors = embedder.embed_batch(["text one", "text two"])
"""
from __future__ import annotations

import logging
from typing import Optional

import requests

log = logging.getLogger(__name__)

_EMBED_ENDPOINT = "/api/embed"       # batch-capable (Ollama ≥ 0.1.x)
_TAGS_ENDPOINT  = "/api/tags"

# How many texts to send per HTTP request. Keeps memory / timeout manageable
# for large ticket/commit lists.
_BATCH_CHUNK = 32


class OllamaEmbedder:
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen3:0.6b",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._available: Optional[bool] = None

    # ── availability check ────────────────────────────────────────────────────

    def is_available(self) -> bool:
        """Return True if the Ollama service is reachable and the model is loaded."""
        if self._available is not None:
            return self._available
        try:
            resp = requests.get(f"{self.base_url}{_TAGS_ENDPOINT}", timeout=5)
            resp.raise_for_status()
            names = {m["name"] for m in resp.json().get("models", [])}
            # match by full name first, then by base name (before ":")
            base = self.model.split(":")[0]
            self._available = self.model in names or any(
                n.split(":")[0] == base for n in names
            )
            if not self._available:
                log.warning(
                    "Ollama model '%s' not found. Available: %s",
                    self.model,
                    sorted(names),
                )
        except Exception as exc:
            log.warning("Ollama not reachable at %s: %s", self.base_url, exc)
            self._available = False
        return self._available

    # ── embedding ─────────────────────────────────────────────────────────────

    def embed(self, text: str) -> Optional[list[float]]:
        """Embed a single string. Returns None on failure."""
        results = self.embed_batch([text])
        return results[0] if results else None

    def embed_batch(
        self,
        texts: list[str],
        chunk_size: int = _BATCH_CHUNK,
    ) -> list[Optional[list[float]]]:
        """Embed a list of strings using Ollama's batch /api/embed endpoint.

        Splits into chunks of `chunk_size` to keep individual requests
        within memory / timeout limits.  Returns a parallel list of vectors
        (None for any text that failed).
        """
        if not texts:
            return []

        results: list[Optional[list[float]]] = []

        for start in range(0, len(texts), chunk_size):
            chunk = texts[start : start + chunk_size]
            chunk_vecs = self._call_embed(chunk)
            results.extend(chunk_vecs)

        return results

    def _call_embed(self, texts: list[str]) -> list[Optional[list[float]]]:
        """Single HTTP call to /api/embed for a chunk of texts."""
        try:
            resp = requests.post(
                f"{self.base_url}{_EMBED_ENDPOINT}",
                json={"model": self.model, "input": texts},
                timeout=120,
            )
            resp.raise_for_status()
            embeddings: list[list[float]] = resp.json().get("embeddings", [])

            if len(embeddings) != len(texts):
                log.warning(
                    "Ollama returned %d embeddings for %d texts; padding with None",
                    len(embeddings),
                    len(texts),
                )

            result: list[Optional[list[float]]] = list(embeddings)
            while len(result) < len(texts):
                result.append(None)
            return result

        except Exception as exc:
            log.warning("Ollama embed request failed: %s", exc)
            return [None] * len(texts)
