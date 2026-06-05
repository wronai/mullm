"""Hybrid routing: nlp2cmd przed regułami file_list."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app import prompt_router as pr
from app.routing_schemas import Nlp2CmdQueryResponse, NlpCommandAnalysis, build_nlp2cmd_request


def _analysis(command: str, confidence: float = 0.9) -> NlpCommandAnalysis:
    req = build_nlp2cmd_request("test")
    resp = Nlp2CmdQueryResponse(
        success=True,
        command=command,
        confidence=confidence,
        domain="shell",
        intent="list",
    )
    return NlpCommandAnalysis(request=req, response=resp)


@pytest.mark.asyncio
async def test_hybrid_nlp2cmd_prefers_shell_over_file_list(monkeypatch):
    monkeypatch.setenv("PROMPT_ROUTER_MODE", "hybrid")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    with patch(
        "app.prompt_router.analyze_shell_nl",
        new_callable=AsyncMock,
        return_value=_analysis("ls -la ~"),
    ):
        # Bez słów „lista plików” — reguły mogą mylić z file_list, nlp2cmd rozstrzyga shell
        d = await pr.decide_route("pokaż zawartość katalogu domowego użytkownika")
    assert d.route == "nlp2cmd_shell"
    assert d.policy_flags.get("shell_plugin") == "nlp2cmd"
    assert "routing_nlp2cmd" in d.reason_codes
    assert d.policy_flags.get("nlp2cmd_analysis", {}).get("source") == "nlp2cmd"


@pytest.mark.asyncio
async def test_hybrid_prefers_host_shell_for_lista_plikow_usera(monkeypatch):
    monkeypatch.setenv("PROMPT_ROUTER_MODE", "hybrid")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    with patch(
        "app.prompt_router.analyze_shell_nl",
        new_callable=AsyncMock,
        return_value=_analysis("ls -la ~", confidence=0.95),
    ):
        d = await pr.decide_route("lista plikow usera")
    assert d.route == "nlp2cmd_shell"
    assert d.policy_flags.get("local_analysis_parallel") is True
    assert d.policy_flags.get("routing_llm_skipped") == "local_sufficient"


@pytest.mark.asyncio
async def test_hybrid_keeps_file_list_when_registry_hint(monkeypatch):
    monkeypatch.setenv("PROMPT_ROUTER_MODE", "hybrid")
    with patch(
        "app.prompt_router.analyze_shell_nl",
        new_callable=AsyncMock,
        return_value=_analysis("ls -la", confidence=0.95),
    ):
        d = await pr.decide_route("lista plikow usera z rejestru access fabric")
    assert d.route == "mullm_file_list"


@pytest.mark.asyncio
async def test_hybrid_without_nlp2cmd_falls_back_expectations(monkeypatch):
    monkeypatch.setenv("PROMPT_ROUTER_MODE", "hybrid")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    with patch(
        "app.prompt_router.analyze_shell_nl",
        new_callable=AsyncMock,
        return_value=None,
    ):
        d = await pr.decide_route("lista plikow usera")
    assert d.route == "nlp2cmd_shell"
    assert d.policy_flags.get("expectation_id") == "shell_host_user_files"


@pytest.mark.asyncio
async def test_local_sufficient_skips_openrouter(monkeypatch):
    monkeypatch.setenv("PROMPT_ROUTER_MODE", "hybrid")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    with (
        patch(
            "app.prompt_router.analyze_shell_nl",
            new_callable=AsyncMock,
            return_value=_analysis("ls -la ~", confidence=0.95),
        ),
        patch(
            "app.prompt_router.decide_route_llm",
            new_callable=AsyncMock,
        ) as llm_mock,
    ):
        d = await pr.decide_route("lista plikow usera")
    llm_mock.assert_not_called()
    assert d.policy_flags.get("routing_llm_skipped") == "local_sufficient"


@pytest.mark.asyncio
async def test_shell_nl_rules_local_route(monkeypatch):
    monkeypatch.setenv("PROMPT_ROUTER_MODE", "rules")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    d = pr.decide_route_rules("sprawdz miejsce na dysku")
    assert d.route == "nlp2cmd_shell"
    assert "ingress_shell_nl" in d.reason_codes
