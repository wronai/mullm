from __future__ import annotations

import urllib.request

from app.access.adapters.base import AdapterResult, ResourceAdapter
from app.access.uri import MullmUri


class HttpAdapter(ResourceAdapter):
    async def probe(self, uri: MullmUri) -> AdapterResult:
        url = self._to_url(uri)
        try:
            request = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(request, timeout=10) as response:
                return AdapterResult(
                    ok=True,
                    content_type=response.headers.get("Content-Type"),
                    size_bytes=int(response.headers.get("Content-Length", 0) or 0),
                    metadata={"url": url, "status": response.status},
                )
        except Exception:
            return await self.fetch(uri, max_bytes=0)

    async def fetch(self, uri: MullmUri, *, max_bytes: int = 65536) -> AdapterResult:
        url = self._to_url(uri)
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                body = response.read(max_bytes)
                return AdapterResult(
                    ok=True,
                    content_type=response.headers.get("Content-Type"),
                    size_bytes=len(body),
                    body_preview=body.decode("utf-8", errors="replace"),
                    metadata={"url": url, "status": response.status},
                )
        except Exception as exc:
            return AdapterResult(ok=False, error=str(exc))

    async def copy_to_local(self, uri: MullmUri, destination_path: str) -> AdapterResult:
        result = await self.fetch(uri)
        if not result.ok or not result.body_preview:
            return result
        with open(destination_path, "w", encoding="utf-8") as handle:
            handle.write(result.body_preview)
        return AdapterResult(ok=True, metadata={"dest": destination_path})

    def _to_url(self, uri: MullmUri) -> str:
        adapter = uri.adapter if uri.adapter in {"http", "https"} else "https"
        return f"{adapter}://{uri.path}" + (f"?{uri.query}" if uri.query else "")
