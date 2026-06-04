"""Tests for nlp2dsl_bridge routing → policy_flags (PR-C)."""

from __future__ import annotations

from app.nlp2dsl_bridge import (
    intent_routing_policy_flags,
    merge_intent_into_policy_flags,
    routing_from_response,
)


def test_routing_from_response():
    assert routing_from_response({"routing": {"action": "send_invoice", "source": "rules"}}) == {
        "action": "send_invoice",
        "source": "rules",
    }
    assert routing_from_response({}) is None


def test_intent_routing_policy_flags():
    flags = intent_routing_policy_flags(
        {
            "action": "send_invoice",
            "intent": "send_invoice",
            "source": "rules",
            "confidence": 0.88,
            "authorized": True,
            "reason_codes": ["parser_rules"],
        }
    )
    assert flags["nlp2dsl_action"] == "send_invoice"
    assert flags["nlp2dsl_source"] == "rules"
    assert flags["nlp2dsl_confidence"] == 0.88


def test_merge_intent_into_policy_flags():
    pf: dict = {}
    merge_intent_into_policy_flags(
        pf,
        {"action": "mullm_shell_task", "source": "native_routing", "authorized": True},
    )
    assert pf["nlp2dsl_action"] == "mullm_shell_task"
    assert pf["nlp2dsl_source"] == "native_routing"
