from app.api_routes import router


def test_api_router_keeps_public_workspace_paths():
    paths = {route.path for route in router.routes}

    assert "/chat/message" in paths
    assert "/files/upload" in paths
    assert "/tickets/{task_id}/confirm" in paths
    assert "/workspace/logs/export" in paths
    assert "/agent-workroom/{workroom_id}/run" in paths
    assert "/access/matrix" in paths
    assert "/router/decide" in paths
