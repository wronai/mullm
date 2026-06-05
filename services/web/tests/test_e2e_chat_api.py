"""
E2E routingu czatu przez HTTP API (in-process ASGI via httpx.AsyncClient).

Pełna ścieżka: POST /api/chat/session → POST /api/chat/message → export logów.
Bez UI i bez Docker — orchestrator/RAG mockowane tam gdzie trzeba.

Używa httpx.ASGITransport zamiast starlette.TestClient, żeby nie wymagać
anyio.from_thread (psuje się przy anyio 4.x w venv Koru / mieszanych pinach).
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest


@pytest.fixture
async def api_client() -> AsyncIterator[httpx.AsyncClient]:
    try:
        from app.main import app
    except RuntimeError as exc:
        if "python-multipart" in str(exc):
            pytest.skip("pip install -r services/web/requirements.txt (python-multipart)")
        raise
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def _start_session(client: httpx.AsyncClient) -> str:
    r = await client.post("/api/chat/session", json={})
    assert r.status_code == 200, r.text
    return r.json()["session_id"]


async def _chat(
    client: httpx.AsyncClient, session_id: str, message: str, *, use_rag: bool = False
) -> dict:
    r = await client.post(
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

    async def test_host_file_list_via_orient(
        self,
        api_client: httpx.AsyncClient,
        patch_shell_task,
    ) -> None:
        sid = await _start_session(api_client)
        out = await _chat(api_client, sid, "lista plikow usera")

        routing = out.get("routing") or {}
        assert routing.get("route") == "nlp2cmd_shell"
        assert routing.get("nlp2dsl_orient") is True
        assert "nlp2dsl orient" in (out.get("reply") or "").lower() or "ls -la" in (out.get("reply") or "")

    async def test_registry_file_list_full_api_path(
        self,
        api_client: httpx.AsyncClient,
        patch_file_inventory,
        patch_nlp2dsl_down,
    ) -> None:
        sid = await _start_session(api_client)
        out = await _chat(api_client, sid, "lista plikow usera z rejestru access fabric")

        assert out.get("intent") == "file_list"
        assert "RAG Smoke" in (out.get("reply") or "")
        routing = out.get("routing") or {}
        assert routing.get("route") == "mullm_file_list"
        assert routing.get("nlp2dsl_orient") is True

        logs = await api_client.get(f"/api/workspace/logs/export?session_id={sid}")
        assert logs.status_code == 200
        text = logs.json().get("text") or ""
        assert "mullm_file_list" in text

    async def test_file_list_registry_scope_stays_mullm_file_list(
        self,
        api_client: httpx.AsyncClient,
        patch_file_inventory,
        patch_nlp2dsl_down,
    ) -> None:
        """Jawny rejestr → mullm_file_list (rules mode w testach)."""
        sid = await _start_session(api_client)
        out = await _chat(api_client, sid, "lista plikow usera z rejestru access fabric")
        routing = out.get("routing") or {}
        assert routing.get("route") == "mullm_file_list"
        assert out.get("task") is None

    async def test_router_file_list_rules_mode(
        self, api_client: httpx.AsyncClient
    ) -> None:
        r = await api_client.get(
            "/api/router/decide",
            params={"message": "lista plikow usera z rejestru", "use_rag": "false"},
        )
        body = r.json()
        assert body["route"] == "mullm_file_list"
        assert body["route"] != "mullm_shell"

    async def test_router_run_ls_home_is_shell(self, api_client: httpx.AsyncClient) -> None:
        """Listing ~/ via host filesystem = explicit shell prefix, not file_list intent."""
        r = await api_client.get(
            "/api/router/decide",
            params={"message": "run ls -la ~", "use_rag": "false"},
        )
        assert r.status_code == 200
        assert r.json()["route"] == "mullm_shell"

    async def test_continue_clarify_not_unknown(
        self,
        api_client: httpx.AsyncClient,
        patch_file_inventory,
        patch_nlp2dsl_down,
    ) -> None:
        sid = await _start_session(api_client)
        out = await _chat(api_client, sid, "kontynuuj")

        assert "Nie rozpoznałem intencji" not in (out.get("reply") or "")
        routing = out.get("routing") or {}
        assert routing.get("route") in ("workroom_hint", "mullm_continue")
        assert "intent_continue" in (routing.get("reason_codes") or [])

    async def test_router_decide_dry_run_file_list(self, api_client: httpx.AsyncClient) -> None:
        r = await api_client.get(
            "/api/router/decide",
            params={
                "message": "lista plikow usera z rejestru",
                "mode": "discuss",
                "use_rag": "false",
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body["route"] == "mullm_file_list"
        assert body["confidence"] >= 0.9

    async def test_routing_feedback_on_turn(
        self,
        api_client: httpx.AsyncClient,
        patch_file_inventory,
        patch_nlp2dsl_down,
    ) -> None:
        sid = await _start_session(api_client)
        out = await _chat(api_client, sid, "lista plikow usera z rejestru")
        turn_id = (out.get("routing") or {}).get("turn_id")
        assert turn_id
        r = await api_client.post(
            "/api/routing/feedback",
            json={
                "session_id": sid,
                "turn_id": turn_id,
                "rating": "bad",
                "expected_route": "mullm_file_list",
                "improvement_notes": "test",
            },
        )
        assert r.status_code == 200
        assert r.json().get("improvement_ticket_id")

    async def test_routing_explain_file_list_tree(
        self, api_client: httpx.AsyncClient, monkeypatch
    ) -> None:
        monkeypatch.setenv("PROMPT_ROUTER_MODE", "rules")
        r = await api_client.get(
            "/api/routing/explain",
            params={"message": "lista plikow usera", "mode": "discuss", "use_rag": "false"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body.get("schema") == "mullm.routing.decision_tree.v1"
        orient = next(s for s in body["steps"] if s["step"] == "nlp2dsl_orient")
        assert orient["status"] == "selected"
        assert body.get("selected_step") == "nlp2dsl_orient"
        assert any(
            e["id"] in ("shell_host_user_files", "file_list_user_scope_registry")
            for e in body.get("matched_expectations") or []
        )

    async def test_routing_schemas_endpoint(self, api_client: httpx.AsyncClient) -> None:
        r = await api_client.get("/api/routing/schemas")
        assert r.status_code == 200
        body = r.json()
        assert body.get("bundle_id") == "mullm.routing.schemas.v1"
        assert "nlp2cmd" in body
        assert "openrouter_classifier" in body

    async def test_routing_policy_endpoint(self, api_client: httpx.AsyncClient) -> None:
        r = await api_client.get("/api/routing/policy")
        assert r.status_code == 200
        order = r.json().get("ingress_order") or []
        assert "rules" in order
        assert "agent_shell" in order
        assert order.index("agent_shell") < order.index("nlp2dsl")
        assert r.json()["agents"]["by_route"]["nlp2cmd_shell"] == "shell_agent"

    async def test_agents_status_endpoint(self, api_client: httpx.AsyncClient) -> None:
        r = await api_client.get("/api/agents/status")
        assert r.status_code == 200
        ids = {a["id"] for a in r.json().get("agents") or []}
        assert ids == {"nlp2cmd", "nlp2dsl"}

    async def test_shell_nl_uses_nlp2cmd_plugin(
        self,
        api_client: httpx.AsyncClient,
        patch_nlp2cmd_translate,
        patch_shell_task,
        patch_nlp2dsl_down,
    ) -> None:
        sid = await _start_session(api_client)
        out = await _chat(api_client, sid, "sprawdz miejsce na dysku")
        routing = out.get("routing") or {}
        assert routing.get("route") == "nlp2cmd_shell"
        assert routing.get("shell_plugin") == "nlp2cmd"
        assert routing.get("nlp2dsl_orient") is True
        assert routing.get("shell_translation_source") == "nlp2cmd"
        assert out.get("executed") == "nlp2cmd_shell"
        assert (routing.get("nlp2cmd") or {}).get("command") == "df -h"
