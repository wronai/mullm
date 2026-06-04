from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.access.uri import MullmUri


@dataclass
class AdapterResult:
    ok: bool
    content_type: str | None = None
    size_bytes: int = 0
    metadata: dict[str, Any] | None = None
    error: str | None = None
    body_preview: str | None = None


class ResourceAdapter(ABC):
    @abstractmethod
    async def probe(self, uri: MullmUri) -> AdapterResult:
        """Sprawdza dostępność zasobu i zwraca metadane."""

    @abstractmethod
    async def fetch(self, uri: MullmUri, *, max_bytes: int = 65536) -> AdapterResult:
        """Pobiera fragment treści zasobu."""

    @abstractmethod
    async def copy_to_local(
        self, uri: MullmUri, destination_path: str
    ) -> AdapterResult:
        """Kopiuje zasób do lokalnej ścieżki (sandbox transport)."""
