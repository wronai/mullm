"""
E2E routingu czatu przez HTTP API (in-process TestClient).

Pełna ścieżka: POST /api/chat/session → POST /api/chat/message → export logów.
Bez UI i bez Docker — orchestrator/RAG mockowane tam gdzie trzeba.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def api_client() -> TestClient:
    try:
        from app.main import app
    except RuntimeError as exc:
        if "python-multipart" in str(exc):
            pytest.skip("pip install -r services/web/requirements.txt (python-multipart)")
        raise
    with TestClient(app) as client:
        yield client


def _start_session(client) -> str:
    r = client.post("/api/chat/session", json={})
    assert r.status_code == 200, r.text
    return r.json()["session_id"]


def _chat(client, session_id: str, message: str, *, use_rag: bool = False) -> dict:
    r = client.post(
        "/api/chat/message",
        json={
            "session_id": session_id,
            "message": message,
            "mode": "discuss",
            "use_rag": use_rag,
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


class TestE2EChatRoutingApi:
    """Scenariusze z exportu workspace (file list, kontynuuj)."""

    def test_file_list_full_api_path(
        self,
        api_client,
        patch_file_inventory,
        patch_nlp2dsl_down,
    ) -> None:
        sid = _start_session(api_client)
        out = _chat(api_client, sid, "lista plikow usera")

        assert out.get("intent") == "file_list"
        assert "RAG Smoke" in (out.get("reply") or "")
        routing = out.get("routing") or {}
        assert routing.get("route") == "mullm_file_list"
        assert routing.get("nlp2dsl_skipped") is True
        assert "intent_file_list" in (routing.get("reason_codes") or [])

        logs = api_client.get(f"/api/workspace/logs/export?session_id={sid}")
        assert logs.status_code == 200
        text = logs.json().get("text") or ""
        assert "mullm_file_list" in text
        assert "nlp2dsl: skipped" in text
        assert "mullm_shell" not in text or "executed=shell" not in text.lower()

    def test_file_list_does_not_use_shell_for_home_directory(
        self,
        api_client,
        patch_file_inventory,
        patch_nlp2dsl_down,
    ) -> None:
        """
        „lista plikow usera” = rejestr Access Fabric (scope=user), nie ls ~ przez shell agent.

        Shell do katalogu domowego: osobna komenda, np. ``run ls -la ~``.
        """
        sid = _start_session(api_client)
        out = _chat(api_client, sid, "lista plikow usera")
        reply = (out.get("reply") or "").lower()
        routing = out.get("routing") or {}

        assert routing.get("route") == "mullm_file_list"
        assert routing.get("route") != "mullm_shell"
        assert out.get("executed") != "mullm_shell"
        assert out.get("task") is None
        assert "rejestr" in reply or "access fabric" in reply
        assert "nie shell" in reply
        assert "~/." not in reply and "katalog domowy" not in reply

    def test_router_file_list_is_not_shell_decide(self, api_client) -> None:
        r = api_client.get(
            "/api/router/decide",
            params={"message": "lista plikow usera", "use_rag": "false"},
        )
        body = r.json()
        assert body["route"] == "mullm_file_list"
        assert body["route"] != "mullm_shell"

    def test_router_run_ls_home_is_shell(self, api_client) -> None:
        """Listing ~/ via host filesystem = explicit shell prefix, not file_list intent."""
        r = api_client.get(
            "/api/router/decide",
            params={"message": "run ls -la ~", "use_rag": "false"},
        )
        assert r.status_code == 200
        assert r.json()["route"] == "mullm_shell"

    def test_continue_clarify_not_unknown(
        self,
        api_client,
        patch_file_inventory,
        patch_nlp2dsl_down,
    ) -> None:
        sid = _start_session(api_client)
        out = _chat(api_client, sid, "kontynuuj")

        assert "Nie rozpoznałem intencji" not in (out.get("reply") or "")
        routing = out.get("routing") or {}
        assert routing.get("route") in ("workroom_hint", "mullm_continue")
        assert "intent_continue" in (routing.get("reason_codes") or [])

    def test_router_decide_dry_run_file_list(self, api_client) -> None:
        r = api_client.get(
            "/api/router/decide",
            params={"message": "lista plikow usera", "mode": "discuss", "use_rag": "false"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["route"] == "mullm_file_list"
        assert body["confidence"] >= 0.9

    def test_routing_policy_endpoint(self, api_client) -> None:
        r = api_client.get("/api/routing/policy")
        assert r.status_code == 200
        order = r.json().get("ingress_order") or []
        assert "rules" in order
        assert "agent_shell" in order
        assert order.index("agent_shell") < order.index("nlp2dsl")
        assert r.json()["agents"]["by_route"]["nlp2cmd_shell"] == "shell_agent"

    def test_agents_status_endpoint(self, api_client) -> None:
        r = api_client.get("/api/agents/status")
        assert r.status_code == 200
        ids = {a["id"] for a in r.json().get("agents") or []}
        assert ids == {"nlp2cmd", "nlp2dsl"}

    def test_shell_nl_uses_nlp2cmd_plugin(
        self,
        api_client,
        patch_nlp2cmd_translate,
        patch_shell_task,
        patch_nlp2dsl_down,
    ) -> None:
        sid = _start_session(api_client)
        out = _chat(api_client, sid, "sprawdz miejsce na dysku")
        routing = out.get("routing") or {}
        assert routing.get("route") == "nlp2cmd_shell"
        assert routing.get("shell_plugin") == "nlp2cmd"
        assert routing.get("nlp2dsl_skipped") is True
        assert out.get("executed") == "nlp2cmd_shell"
        assert (routing.get("nlp2cmd") or {}).get("command") == "df -h"
