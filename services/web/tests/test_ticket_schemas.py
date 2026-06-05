"""Standardy ticketów + most planfile."""

from __future__ import annotations

from unittest.mock import patch

from app.planfile_bridge import _build_create_cmd, sync_improvement_ticket
from app.ticket_schemas import ImprovementTicket, schemas_bundle


def test_ticket_schemas_bundle() -> None:
    bundle = schemas_bundle()
    assert bundle["bundle_id"] == "mullm.tickets.schemas.v1"
    assert "improvement" in bundle["kinds"]
    assert bundle["planfile_mapping"]["improvement"]["source"] == "mullm.routing"


def test_improvement_planfile_cmd() -> None:
    t = ImprovementTicket(
        ticket_id="abc",
        session_id="s1",
        turn_id="turn-1",
        rating="bad",
        user_message="lista plikow usera",
        actual_route="nlp2cmd_shell",
        expected_route="mullm_file_list",
        expected_reply_hint="rejestr nie ls",
        suggested_actions=["Dopisz regułę"],
        created_at="2026-01-01T00:00:00Z",
    )
    cmd = _build_create_cmd(t)
    assert "planfile" in cmd[0]
    assert "mullm.routing" in cmd
    assert "dedupe:mullm-routing-turn-1" in cmd


def test_sync_disabled_without_env() -> None:
    with patch.dict("os.environ", {}, clear=True):
        assert sync_improvement_ticket({"ticket_id": "x"}) is None
