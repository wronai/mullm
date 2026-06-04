from app.access.adapters.base import AdapterResult, ResourceAdapter
from app.access.adapters.http_adapter import HttpAdapter
from app.access.adapters.localfs import LocalFsAdapter

__all__ = ["AdapterResult", "ResourceAdapter", "HttpAdapter", "LocalFsAdapter", "get_adapter"]


def get_adapter(name: str) -> ResourceAdapter:
    adapters = {
        "localfs": LocalFsAdapter(),
        "http": HttpAdapter(),
        "https": HttpAdapter(),
    }
    adapter = adapters.get(name)
    if not adapter:
        raise ValueError(f"Unknown adapter: {name}")
    return adapter
