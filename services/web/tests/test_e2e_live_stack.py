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
import time

import httpx
import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("MULLM_E2E"),
    reason="Set MULLM_E2E=1 and start stack (web :3003)",
)

BASE = os.getenv("MULLM_E2E_BASE_URL", "http://127.0.0.1:3003").rstrip("/")
TIMEOUT = float(os.getenv("MULLM_E2E_TIMEOUT", "60"))
_WAIT_SECONDS = float(os.getenv("MULLM_E2E_WAIT_SECONDS", "90"))
_WAIT_INTERVAL = float(os.getenv("MULLM_E2E_WAIT_INTERVAL", "1"))


def _wait_for_web_ready() -> None:
    """Po `docker compose up -d web` uvicorn potrzebuje chwili — unikaj connection reset."""
    if os.getenv("MULLM_E2E_SKIP_WAIT", "").strip().lower() in ("1", "true", "yes"):
        return
    deadline = time.monotonic() + _WAIT_SECONDS
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            r = httpx.get(f"{BASE}/health", timeout=5.0)
            if r.status_code == 200 and r.json().get("service") == "mullm-web":
                return
        except httpx.HTTPError as exc:
            last_err = exc
        time.sleep(_WAIT_INTERVAL)
    msg = f"web not ready at {BASE}/health within {_WAIT_SECONDS}s"
    if last_err:
        raise AssertionError(f"{msg} (last: {last_err})") from last_err
    raise AssertionError(msg)


@pytest.fixture(scope="session", autouse=True)
def _live_stack_ready() -> None:
    if os.getenv("MULLM_E2E"):
        _wait_for_web_ready()


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
    assert routing.get("route") in ("mullm_file_list", "nlp2cmd_shell"), body
    assert "plik" in (body.get("reply") or "").lower() or "RAG" in (body.get("reply") or "")

    r = http.get("/api/workspace/logs/export", params={"session_id": sid})
    assert r.status_code == 200
    assert "mullm_file_list" in (r.json().get("text") or "")


def test_live_file_list_host_or_registry(http: httpx.Client) -> None:
    """Hybrid: lista plików usera → nlp2cmd_shell (ls ~) lub starszy stack → mullm_file_list."""
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
    assert routing.get("route") in ("mullm_file_list", "nlp2cmd_shell")
    assert routing.get("route") != "mullm_shell"


def test_live_shell_route_for_run_ls_home(http: httpx.Client) -> None:
    r = http.get(
        "/api/router/decide",
        params={"message": "run ls -la ~", "use_rag": "false"},
    )
    route = r.json()["route"]
    # hybrid + healthy nlp2cmd → nlp2cmd_shell; rules-only → mullm_shell
    assert route in ("nlp2cmd_shell", "mullm_shell")


def test_live_router_decide(http: httpx.Client) -> None:
    r = http.get(
        "/api/router/decide",
        params={"message": "lista plikow usera", "use_rag": "false"},
    )
    assert r.status_code == 200
    assert r.json()["route"] in ("mullm_file_list", "nlp2cmd_shell")


def test_live_routing_explain_file_list(http: httpx.Client) -> None:
    r = http.get(
        "/api/routing/explain",
        params={"message": "lista plikow usera", "mode": "discuss", "use_rag": "false"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("selected_step") == "rules"
    assert any(
        e.get("id") in ("shell_host_user_files", "file_list_user_scope", "file_list_user_scope_registry")
        for e in body.get("matched_expectations") or []
    )


def test_live_chat_includes_decision_tree(http: httpx.Client) -> None:
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
    assert r.status_code == 200
    tree = (r.json().get("routing") or {}).get("decision_tree")
    assert tree and tree.get("selected_step") == "rules"


def test_live_routing_policy_has_routes(http: httpx.Client) -> None:
    r = http.get("/api/routing/policy", params={"reload": "true"})
    assert r.status_code == 200
    body = r.json()
    by_route = (body.get("agents") or {}).get("by_route") or {}
    assert by_route.get("mullm_file_list") == "files_agent"
    assert by_route.get("nlp2cmd_shell") == "shell_agent"
    assert "agent_shell" in (body.get("ingress_order") or [])
    plugins = body.get("agent_plugins") or []
    assert any(p.get("id") == "nlp2cmd" for p in plugins)


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
