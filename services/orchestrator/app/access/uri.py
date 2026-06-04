from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote, unquote


SCHEMES = ("mullm",)


@dataclass(frozen=True)
class MullmUri:
    scheme: str
    adapter: str
    path: str
    query: str = ""

    @property
    def canonical(self) -> str:
        base = f"{self.scheme}://{self.adapter}/{self.path}"
        if self.query:
            return f"{base}?{self.query}"
        return base


def parse_uri(uri: str) -> MullmUri:
    if not uri.startswith("mullm://"):
        raise ValueError(f"Invalid mullm URI: {uri}")
    rest = uri.removeprefix("mullm://")
    if "?" in rest:
        body, query = rest.split("?", 1)
    else:
        body, query = rest, ""
    parts = body.split("/", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(f"Invalid mullm URI path: {uri}")
    adapter, path = parts[0], unquote(parts[1])
    return MullmUri(scheme="mullm", adapter=adapter, path=path, query=query)


def build_uri(adapter: str, path: str, *, query: str = "") -> str:
    encoded = quote(path, safe="/-_.~")
    base = f"mullm://{adapter}/{encoded}"
    return f"{base}?{query}" if query else base
