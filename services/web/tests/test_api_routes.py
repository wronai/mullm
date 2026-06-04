import pytest

from app.api_routes import router


@pytest.mark.parametrize(
    "path",
    [
        "/chat/message",
        "/files/upload",
        "/tickets/{task_id}/confirm",
        "/workspace/logs/export",
        "/agent-workroom/{workroom_id}/run",
        "/access/matrix",
        "/router/decide",
    ],
)
def test_api_router_keeps_public_workspace_paths(path):
    paths = {route.path for route in router.routes}
    assert path in paths
