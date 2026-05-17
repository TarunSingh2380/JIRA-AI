"""Ollama BGE-M3 embedding client.

Calls the locally-hosted Ollama service to generate 1024-dimensional dense
vector embeddings using the BGE-M3 model.

Usage:
    embedder = OllamaEmbedder()
    if embedder.is_available():
        vectors = embedder.embed_batch(["text one", "text two"])
"""
from __future__ import annotations

import logging
import time
from typing import Optional

import requests

log = logging.getLogger(__name__)

_EMBED_ENDPOINT = "/api/embeddings"
_TAGS_ENDPOINT = "/api/tags"


class OllamaEmbedder:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "bge-m3") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._available: Optional[bool] = None

    def is_available(self) -> bool:
        """Check whether the Ollama service has the configured model loaded."""
        if self._available is not None:
            return self._available
        try:
            resp = requests.get(f"{self.base_url}{_TAGS_ENDPOINT}", timeout=5)
            resp.raise_for_status()
            model_names = {m["name"].split(":")[0] for m in resp.json().get("models", [])}
            self._available = self.model.split(":")[0] in model_names
            if not self._available:
                log.warning(
                    "Ollama model '%s' not found. Available: %s",
                    self.model,
                    sorted(model_names),
                )
        except Exception as exc:
            log.warning("Ollama not reachable at %s: %s", self.base_url, exc)
            self._available = False
        return self._available

    def embed(self, text: str) -> Optional[list[float]]:
        """Embed a single string. Returns None on any failure."""
        try:
            resp = requests.post(
                f"{self.base_url}{_EMBED_ENDPOINT}",
                json={"model": self.model, "prompt": text},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json().get("embedding")
        except Exception as exc:
            log.debug("Ollama embed error: %s", exc)
            return None

    def embed_batch(
        self,
        texts: list[str],
        inter_request_ms: int = 20,
    ) -> list[Optional[list[float]]]:
        """Embed a list of strings sequentially. Returns parallel list of vectors (None on failure)."""
        results: list[Optional[list[float]]] = []
        for i, text in enumerate(texts):
            results.append(self.embed(text))
            if inter_request_ms > 0 and i < len(texts) - 1:
                time.sleep(inter_request_ms / 1000.0)
        return results
