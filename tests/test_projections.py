import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

def _project_event():
    root = Path(__file__).resolve().parents[1] / "services" / "projector"
    saved = {key: sys.modules[key] for key in list(sys.modules) if key == "app" or key.startswith("app.")}
    for key in saved:
        del sys.modules[key]
    sys.path.insert(0, str(root))
    try:
        from app.projections.dispatcher import project_event as fn

        return fn
    finally:
        for key in list(sys.modules):
            if key == "app" or key.startswith("app."):
                del sys.modules[key]
        sys.modules.update(saved)


class RecordingDB:
    def __init__(self) -> None:
        self.queries: list[tuple[str, tuple]] = []

    async def execute(self, query: str, *args) -> str:
        self.queries.append((query.strip(), args))
        return "OK"


def _event(event_type: str, aggregate_type: str, aggregate_id: str, payload: dict) -> dict:
    return {
        "event_id": "evt-1",
        "stream_id": f"{aggregate_type}-{aggregate_id}",
        "aggregate_type": aggregate_type,
        "aggregate_id": aggregate_id,
        "event_type": event_type,
        "occurred_at": datetime.now(timezone.utc),
        "payload": payload,
        "metadata": {"actor": {"type": "user", "id": "admin"}},
    }


@pytest.mark.asyncio
async def test_task_created_updates_task_board_and_feed():
    db = RecordingDB()
    await _project_event()(
        db,
        _event(
            "TaskCreated",
            "task",
            "task-1",
            {
                "task_id": "task-1",
                "title": "Deploy",
                "priority": "high",
                "execution_mode": "semi_auto",
                "status": "pending",
            },
        ),
    )
    sql_blocks = " ".join(query for query, _ in db.queries)
    assert "operational_feed" in sql_blocks
    assert "task_board" in sql_blocks


@pytest.mark.asyncio
async def test_approval_requested_projection():
    db = RecordingDB()
    await _project_event()(
        db,
        _event(
            "ApprovalRequested",
            "approval",
            "apr-1",
            {
                "approval_id": "apr-1",
                "action_type": "ActivatePlugin",
                "target_id": "plugin-x",
                "requested_by": "user-1",
                "status": "pending",
            },
        ),
    )
    assert any("approval_requests" in query for query, _ in db.queries)
