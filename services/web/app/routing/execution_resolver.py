"""Mapuje OrientationDecision → RouteDecision Mullm."""

from __future__ import annotations

from typing import Any

from app import prompt_router
from app.routing.decision import OrientationDecision


def route_from_orientation(
    orient: OrientationDecision | dict[str, Any],
) -> prompt_router.RouteDecision | None:
    if isinstance(orient, dict):
        parsed = OrientationDecision.from_dict(orient)
        if parsed is None:
            return None
        orient = parsed

    if not orient.is_actionable:
        return None

    codes = list(orient.reason_codes)
    flags: dict[str, Any] = {
        "nlp2dsl_orientation": orient.to_dict(),
        "pipeline_step": "nlp2dsl_orient",
        "orientation_source": orient.source,
    }

    if orient.category == "file_list_registry":
        return prompt_router.RouteDecision(
            route="mullm_file_list",
            handler="conductor._mullm_file_list_turn",
            intent="file_list",
            confidence=orient.confidence,
            reason="nlp2dsl orient → rejestr Access Fabric",
            reason_codes=codes + ["nlp2dsl_orient"],
            list_scope=orient.list_scope or "user",
            policy_flags=flags,
            router_mode="orientation",
        )

    shell_cmd = (orient.shell_command or "").strip()
    if orient.category in ("file_list_host", "shell") and shell_cmd:
        flags["shell_plugin"] = "nlp2dsl_orient"
        flags["shell_translation_source"] = "builtin"
        flags["nlp2cmd_translation"] = {
            "command": shell_cmd,
            "confidence": orient.confidence,
            "domain": "shell",
            "intent": orient.category,
        }
        return prompt_router.RouteDecision(
            route="nlp2cmd_shell",
            handler="workspace.create_task_immediate",
            intent="shell_orient",
            confidence=orient.confidence,
            reason=f"nlp2dsl orient → `{shell_cmd[:120]}`",
            reason_codes=codes + ["nlp2dsl_orient"],
            policy_flags=flags,
            router_mode="orientation",
        )

    if orient.category == "workflow":
        return prompt_router.RouteDecision(
            route="nlp2dsl",
            handler="nlp2dsl.workflow.chat",
            intent="workflow_orient",
            confidence=orient.confidence,
            reason="nlp2dsl orient → workflow (pełna rozmowa)",
            reason_codes=codes + ["nlp2dsl_orient", "delegate_nlp2dsl"],
            policy_flags=flags,
            router_mode="orientation",
        )

    if orient.category == "shell":
        flags["shell_plugin"] = "nlp2dsl_orient"
        flags["shell_translation_source"] = "nlp2cmd"
        return prompt_router.RouteDecision(
            route="nlp2cmd_shell",
            handler="workspace.create_task_immediate",
            intent="shell_orient",
            confidence=orient.confidence,
            reason="nlp2dsl orient → shell NL (wymaga tłumaczenia nlp2cmd)",
            reason_codes=codes + ["nlp2dsl_orient", "shell_nl_pending"],
            policy_flags=flags,
            router_mode="orientation",
        )

    return None
