"""
E2E na działającym stacku Docker (opcjonalne).

Uruchom:
  docker compose --profile core --profile rag up -d
  MULLM_E2E=1 pytest -o pythonpath=services/web \\
    services/web/tests/test_e2e_live_stack.py -v

Albo: ./scripts/e2e-chat-routing.sh
"""

from __future__ import annotations

import os

import httpx
import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("MULLM_E2E"),
    reason="Set MULLM_E2E=1 and start stack (web :3003)",
)

BASE = os.getenv("MULLM_E2E_BASE_URL", "http://127.0.0.1:3003").rstrip("/")
TIMEOUT = float(os.getenv("MULLM_E2E_TIMEOUT", "60"))


@pytest.fixture
def http() -> httpx.Client:
    with httpx.Client(base_url=BASE, timeout=TIMEOUT) as client:
        yield client


def test_live_health(http: httpx.Client) -> None:
    r = http.get("/health")
    assert r.status_code == 200
    assert r.json().get("service") == "mullm-web"


def test_live_file_list_chat(http: httpx.Client) -> None:
    r = http.post("/api/chat/session", json={})
    assert r.status_code == 200
    sid = r.json()["session_id"]

    r = http.post(
        "/api/chat/message",
        json={
            "session_id": sid,
            "message": "lista plikow usera",
            "mode": "discuss",
            "use_rag": False,
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    routing = body.get("routing") or {}
    assert routing.get("route") == "mullm_file_list", body
    assert "plik" in (body.get("reply") or "").lower() or "RAG" in (body.get("reply") or "")

    r = http.get("/api/workspace/logs/export", params={"session_id": sid})
    assert r.status_code == 200
    assert "mullm_file_list" in (r.json().get("text") or "")


def test_live_file_list_not_shell_route(http: httpx.Client) -> None:
    """Na żywym stacku: lista plików usera nie może iść na mullm_shell (ls ~)."""
    r = http.post("/api/chat/session", json={})
    sid = r.json()["session_id"]
    r = http.post(
        "/api/chat/message",
        json={
            "session_id": sid,
            "message": "lista plikow usera",
            "mode": "discuss",
            "use_rag": False,
        },
    )
    body = r.json()
    routing = body.get("routing") or {}
    assert routing.get("route") == "mullm_file_list"
    assert routing.get("route") != "mullm_shell"
    assert body.get("executed") != "mullm_shell"
    reply = (body.get("reply") or "").lower()
    assert "nie shell" in reply


def test_live_shell_route_for_run_ls_home(http: httpx.Client) -> None:
    r = http.get(
        "/api/router/decide",
        params={"message": "run ls -la ~", "use_rag": "false"},
    )
    assert r.json()["route"] == "mullm_shell"


def test_live_router_decide(http: httpx.Client) -> None:
    r = http.get(
        "/api/router/decide",
        params={"message": "lista plikow usera", "use_rag": "false"},
    )
    assert r.status_code == 200
    assert r.json()["route"] == "mullm_file_list"


def test_live_agents_status_lists_plugins(http: httpx.Client) -> None:
    r = http.get("/api/agents/status")
    assert r.status_code == 200
    ids = {a["id"] for a in r.json().get("agents") or []}
    assert "nlp2cmd" in ids
    assert "nlp2dsl" in ids


def test_live_nlp2cmd_shell_nl(http: httpx.Client) -> None:
    status = http.get("/api/agents/status").json()
    nlp2cmd = next((a for a in status.get("agents") or [] if a.get("id") == "nlp2cmd"), None)
    if not nlp2cmd or not nlp2cmd.get("healthy"):
        pytest.skip("nlp2cmd not healthy (NLP2CMD=1 make up, profile nlp2cmd)")

    r = http.post("/api/chat/session", json={})
    sid = r.json()["session_id"]
    r = http.post(
        "/api/chat/message",
        json={
            "session_id": sid,
            "message": "sprawdz miejsce na dysku",
            "mode": "discuss",
            "use_rag": False,
        },
    )
    body = r.json()
    routing = body.get("routing") or {}
    assert routing.get("route") == "nlp2cmd_shell", body
    assert routing.get("shell_plugin") == "nlp2cmd"
