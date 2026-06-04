from __future__ import annotations

import os
import tempfile
from typing import Any
from uuid import uuid4

from app.access.adapters import get_adapter
from app.access.uri import MullmUri, parse_uri


class TransportService:
    """Access Fabric — probe, fetch, copy między adapterami."""

    def __init__(self, *, sandbox_dir: str | None = None) -> None:
        self._sandbox_override = sandbox_dir

    def _sandbox_dir(self) -> str:
        path = self._sandbox_override or os.getenv(
            "MULLM_TRANSPORT_SANDBOX", "/tmp/mullm-transport"
        )
        os.makedirs(path, exist_ok=True)
        return path

    async def probe(self, uri: str) -> dict[str, Any]:
        parsed = parse_uri(uri)
        adapter = get_adapter(parsed.adapter)
        result = await adapter.probe(parsed)
        return self._result_dict(parsed, result)

    async def fetch(self, uri: str, *, max_bytes: int = 65536) -> dict[str, Any]:
        parsed = parse_uri(uri)
        adapter = get_adapter(parsed.adapter)
        result = await adapter.fetch(parsed, max_bytes=max_bytes)
        return self._result_dict(parsed, result)

    async def copy(self, source_uri: str, dest_uri: str) -> dict[str, Any]:
        """Kopiuje z source do dest (dest musi być localfs w MVP)."""
        source = parse_uri(source_uri)
        dest = parse_uri(dest_uri)
        if dest.adapter != "localfs":
            raise ValueError("MVP transport copy supports localfs destination only")

        src_adapter = get_adapter(source.adapter)
        dest_path = dest.path
        if not os.path.isabs(dest_path):
            dest_path = os.path.join(self._sandbox_dir(), dest_path)
        result = await src_adapter.copy_to_local(source, dest_path)
        return {
            "transfer_id": str(uuid4()),
            "source": source.canonical,
            "destination": dest.canonical,
            "ok": result.ok,
            "error": result.error,
            "metadata": result.metadata or {},
        }

    async def package_to_sandbox(self, source_uri: str) -> dict[str, Any]:
        """Pobiera zasób do izolowanego katalogu sandbox."""
        transfer_id = str(uuid4())
        dest_path = os.path.join(self._sandbox_dir(), transfer_id)
        dest_uri = f"mullm://localfs/{dest_path}"
        outcome = await self.copy(source_uri, dest_uri)
        outcome["transfer_id"] = transfer_id
        outcome["sandbox_path"] = dest_path
        return outcome

    def _result_dict(self, uri: MullmUri, result) -> dict[str, Any]:
        return {
            "uri": uri.canonical,
            "ok": result.ok,
            "content_type": result.content_type,
            "size_bytes": result.size_bytes,
            "metadata": result.metadata or {},
            "error": result.error,
            "body_preview": result.body_preview,
        }
