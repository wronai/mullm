"""Walidacja schematów routingu (nlp2cmd, OpenRouter, agregat Mullm)."""

from __future__ import annotations

import pytest

from app.routing_schemas import (
    Nlp2CmdQueryResponse,
    NlpCommandAnalysis,
    build_nlp2cmd_request,
    llm_system_prompt_with_schema,
    parse_llm_classifier,
    parse_nlp2cmd_response,
    schemas_bundle,
)


def test_schemas_bundle_has_all_libraries() -> None:
    bundle = schemas_bundle()
    assert bundle["bundle_id"] == "mullm.routing.schemas.v1"
    assert "request" in bundle["nlp2cmd"]
    assert "response" in bundle["nlp2cmd"]
    assert "output" in bundle["openrouter_classifier"]
    assert "nlp_analysis" in bundle["mullm"]


def test_parse_nlp2cmd_response_rejects_invalid() -> None:
    assert parse_nlp2cmd_response(None) is None
    assert parse_nlp2cmd_response("not-a-dict") is None
    partial = parse_nlp2cmd_response({"success": True})
    assert partial is not None
    assert not partial.command_text
    parsed = parse_nlp2cmd_response(
        {"success": True, "command": "df -h", "confidence": 0.9}
    )
    assert parsed is not None
    assert parsed.command_text == "df -h"


def test_parse_llm_classifier_valid_and_invalid() -> None:
    ok = parse_llm_classifier(
        {
            "route": "nlp2cmd_shell",
            "intent": "disk_check",
            "confidence": 0.88,
            "reason_codes": ["llm_classifier"],
        }
    )
    assert ok is not None
    assert ok.route == "nlp2cmd_shell"
    assert parse_llm_classifier({"route": "bad_route", "intent": "x", "confidence": 0.5}) is None
    assert parse_llm_classifier({"confidence": 2.0, "route": "rag", "intent": "q"}) is None


def test_llm_prompt_embeds_json_schema() -> None:
    prompt = llm_system_prompt_with_schema()
    assert "mullm.router.llm_classifier" in prompt or "route" in prompt
    assert "JSON" in prompt


def test_nlp_analysis_to_policy_flags() -> None:
    req = build_nlp2cmd_request("df -h")
    resp = Nlp2CmdQueryResponse(
        success=True,
        command="df -h",
        confidence=0.92,
        domain="shell",
        intent="disk",
    )
    analysis = NlpCommandAnalysis(request=req, response=resp)
    flags = analysis.to_policy_flags()
    assert flags["nlp_analysis_schema"] == "mullm.routing.nlp_analysis.v1"
    assert flags["nlp2cmd_translation"]["command"] == "df -h"
    assert flags["nlp2cmd_analysis"]["source"] == "nlp2cmd"
    trans = analysis.to_shell_translation()
    assert trans.command == "df -h"
    assert trans.analysis_schema_id == "mullm.routing.nlp_analysis.v1"
