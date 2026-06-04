import sys
from pathlib import Path


def _projector_app():
    root = Path(__file__).resolve().parents[1] / "services" / "projector"
    saved = {key: sys.modules[key] for key in list(sys.modules) if key == "app" or key.startswith("app.")}
    for key in saved:
        del sys.modules[key]
    sys.path.insert(0, str(root))
    try:
        from app.main import app

        return app
    finally:
        for key in list(sys.modules):
            if key == "app" or key.startswith("app."):
                del sys.modules[key]
        sys.modules.update(saved)


def test_projector_get_routes_are_unique():
    app = _projector_app()
    routes = [
        (route.path, tuple(sorted(route.methods)))
        for route in app.routes
        if hasattr(route, "methods") and "GET" in route.methods
    ]

    assert len(routes) == len(set(routes))
    assert ("/projections/resources", ("GET",)) in routes
    assert ("/projections/rag/documents", ("GET",)) in routes
