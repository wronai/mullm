"""Kontrakt routingu PR-1: orientation_provider + execution_resolver."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.routing.decision import OrientationDecision
from app.routing.execution_resolver import route_from_orientation
from app.routing.ingress_cache import clear_cache, get_cached_orient
from app.routing.orientation_provider import orient_message


def test_orientation_decision_from_dict():
    o = OrientationDecision.from_dict(
        {
            "category": "file_list_host",
            "suggested_action": "mullm_shell_task",
            "confidence": 0.91,
            "shell_command": "ls -la /host-home",
            "source": "local_orient",
        }
    )
    assert o is not None
    assert o.category == "file_list_host"
    assert o.shell_translation_source == "builtin"
    assert o.is_actionable is True


def test_route_from_orientation_registry():
    orient = OrientationDecision(
        category="file_list_registry",
        suggested_action="mullm_list_files",
        confidence=0.93,
        reason_codes=["orientation_file_list_registry"],
        list_scope="user",
        source="nlp2dsl_service",
    )
    d = route_from_orientation(orient)
    assert d is not None
    assert d.route == "mullm_file_list"
    assert d.policy_flags["orientation_source"] == "nlp2dsl_service"


def test_route_from_orientation_shell_builtin():
    orient = OrientationDecision(
        category="file_list_host",
        suggested_action="mullm_shell_task",
        confidence=0.88,
        shell_command="ls -la /host-home",
        source="local_orient",
    )
    d = route_from_orientation(orient)
    assert d is not None
    assert d.route == "nlp2cmd_shell"
    assert d.policy_flags["shell_translation_source"] == "builtin"


def test_route_from_orientation_shell_nl_pending():
    orient = OrientationDecision(
        category="shell",
        suggested_action="mullm_shell_task",
        confidence=0.82,
        source="local_orient",
    )
    d = route_from_orientation(orient)
    assert d is not None
    assert d.route == "nlp2cmd_shell"
    assert d.policy_flags["shell_translation_source"] == "nlp2cmd"


@pytest.mark.asyncio
async def test_orient_message_uses_cache():
    clear_cache()
    payload = {
        "category": "file_list_host",
        "suggested_action": "mullm_shell_task",
        "confidence": 0.9,
        "shell_command": "ls -la /host-home",
        "source": "nlp2dsl_service",
    }
    with patch(
        "app.routing.orientation_provider._orient_remote",
        new_callable=AsyncMock,
        return_value=payload,
    ) as remote:
        first = await orient_message(
            "lista plikow usera",
            session_id="cache-sess",
            chat_mode="discuss",
        )
        second = await orient_message(
            "lista plikow usera",
            session_id="cache-sess",
            chat_mode="discuss",
        )
    assert remote.await_count == 1
    assert first.category == "file_list_host"
    assert second.source == "nlp2dsl_service"
    assert get_cached_orient("cache-sess", "lista plikow usera") is not None
