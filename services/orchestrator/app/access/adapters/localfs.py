from __future__ import annotations

import os
import shutil
from pathlib import Path

from app.access.adapters.base import AdapterResult, ResourceAdapter
from app.access.uri import MullmUri


class LocalFsAdapter(ResourceAdapter):
    def __init__(self, root: str | None = None) -> None:
        self.root = Path(root or os.getenv("MULLM_LOCALFS_ROOT", "/tmp/mullm-access"))

    def _resolve(self, uri: MullmUri) -> Path:
        root = self.root.resolve()
        target = (root / uri.path).resolve()
        if not str(target).startswith(str(root)):
            raise ValueError("Path escapes localfs sandbox")
        return target

    async def probe(self, uri: MullmUri) -> AdapterResult:
        try:
            path = self._resolve(uri)
            if not path.exists():
                return AdapterResult(ok=False, error=f"Not found: {path}")
            stat = path.stat()
            return AdapterResult(
                ok=True,
                content_type="inode/directory" if path.is_dir() else "application/octet-stream",
                size_bytes=stat.st_size,
                metadata={"path": str(path), "is_dir": path.is_dir()},
            )
        except Exception as exc:
            return AdapterResult(ok=False, error=str(exc))

    async def fetch(self, uri: MullmUri, *, max_bytes: int = 65536) -> AdapterResult:
        try:
            path = self._resolve(uri)
            if path.is_dir():
                names = sorted(p.name for p in path.iterdir())[:50]
                preview = "\n".join(names)
                return AdapterResult(
                    ok=True,
                    content_type="text/plain",
                    size_bytes=len(preview),
                    body_preview=preview[:max_bytes],
                    metadata={"listing": True},
                )
            data = path.read_bytes()[:max_bytes]
            return AdapterResult(
                ok=True,
                content_type="application/octet-stream",
                size_bytes=len(data),
                body_preview=data.decode("utf-8", errors="replace"),
            )
        except Exception as exc:
            return AdapterResult(ok=False, error=str(exc))

    async def copy_to_local(self, uri: MullmUri, destination_path: str) -> AdapterResult:
        try:
            src = self._resolve(uri)
            dest = Path(destination_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(src, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dest)
            return AdapterResult(ok=True, metadata={"source": str(src), "dest": str(dest)})
        except Exception as exc:
            return AdapterResult(ok=False, error=str(exc))
