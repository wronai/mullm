from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

OPENROUTER_BASE = "https://openrouter.ai/api/v1"


def normalize_openrouter_model(model: str) -> str:
    """OpenRouter API nie akceptuje prefiksu openrouter/ z lokalnego .env."""
    model = (model or "").strip()
    if model.startswith("openrouter/"):
        return model[len("openrouter/") :]
    return model


class OpenRouterClient:
    """Klient OpenRouter — embeddings i chat (LLM_MODEL z .env)."""

    def __init__(
        self,
        api_key: str | None,
        *,
        llm_model: str,
        embedding_model: str,
        timeout: float = 60.0,
    ) -> None:
        self.api_key = (api_key or "").strip()
        self.llm_model = normalize_openrouter_model(llm_model)
        self.embedding_model = normalize_openrouter_model(embedding_model)
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/wronai/mullm",
            "X-Title": "mullm-rag",
        }

    async def embed(self, texts: list[str]) -> list[list[float]] | None:
        if not self.configured or not texts:
            return None
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{OPENROUTER_BASE}/embeddings",
                    headers=self._headers(),
                    json={"model": self.embedding_model, "input": texts},
                )
                response.raise_for_status()
                data = response.json()
            vectors: list[list[float]] = []
            for item in sorted(data.get("data", []), key=lambda row: row.get("index", 0)):
                vectors.append(item["embedding"])
            return vectors
        except Exception as exc:
            logger.warning("OpenRouter embeddings failed: %s", exc)
            return None

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> tuple[str | None, str | None]:
        """Zwraca (treść, błąd)."""
        if not self.configured:
            return None, "OPENROUTER_API_KEY not set"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{OPENROUTER_BASE}/chat/completions",
                    headers=self._headers(),
                    json={
                        "model": self.llm_model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                if response.status_code >= 400:
                    detail = response.text[:500]
                    logger.warning("OpenRouter chat %s: %s", response.status_code, detail)
                    return None, f"OpenRouter {response.status_code}: {detail}"
                payload = response.json()
            choices = payload.get("choices") or []
            if not choices:
                return None, "empty response from OpenRouter"
            message = choices[0].get("message") or {}
            content = (message.get("content") or "").strip() or None
            return content, None
        except Exception as exc:
            logger.warning("OpenRouter chat failed: %s", exc)
            return None, str(exc)

    async def health(self) -> dict[str, Any]:
        return {
            "configured": self.configured,
            "llm_model": self.llm_model,
            "embedding_model": self.embedding_model,
        }
