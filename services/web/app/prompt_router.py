"""
Jawny router promptu użytkownika → handler Mullm / nlp2dsl / RAG.

Stateless, rules-first (PROMPT_ROUTER_MODE=rules).
Opcjonalnie llm — klasyfikacja OpenRouter tylko gdy włączone i wyższa confidence.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Literal

import httpx

from app import chat as chat_service

RouteKind = Literal[
    "mullm_file_list",
    "mullm_shell",
    "nlp2dsl",
    "rag",
    "workroom_hint",
    "unknown",
]

HandlerKind = Literal[
    "conductor._mullm_file_list_turn",
    "workspace.create_task_immediate",
    "nlp2dsl.workflow.chat",
    "chat.handle_message.rag",
    "conductor._fallback_turn",
    "none",
]

_LLM_HANDLERS: dict[str, HandlerKind] = {
    "mullm_file_list": "conductor._mullm_file_list_turn",
    "mullm_shell": "workspace.create_task_immediate",
    "nlp2dsl": "nlp2dsl.workflow.chat",
    "rag": "chat.handle_message.rag",
    "unknown": "none",
}


@dataclass
class RouteDecision:
    """Audytowalna decyzja routingu (ingress Mullm BFF)."""

    route: RouteKind
    handler: HandlerKind
    intent: str
    confidence: float
    reason: str
    reason_codes: list[str] = field(default_factory=list)
    requires_clarification: bool = False
    fallback_route: RouteKind | None = None
    candidate_routes: list[dict[str, Any]] = field(default_factory=list)
    policy_flags: dict[str, Any] = field(default_factory=dict)
    timing_ms: float = 0.0
    used_llm: bool = False
    router_mode: str = "rules"
    list_scope: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "route": self.route,
            "handler": self.handler,
            "intent": self.intent,
            "confidence": self.confidence,
            "reason": self.reason,
            "reason_codes": self.reason_codes,
            "requires_clarification": self.requires_clarification,
            "fallback_route": self.fallback_route,
            "candidate_routes": self.candidate_routes,
            "policy_flags": self.policy_flags,
            "timing_ms": round(self.timing_ms, 2),
            "used_llm": self.used_llm,
            "router_mode": self.router_mode,
            "list_scope": self.list_scope,
        }


def _candidate(
    route: RouteKind,
    handler: HandlerKind,
    intent: str,
    confidence: float,
    reason_codes: list[str],
    **extra: Any,
) -> dict[str, Any]:
    return {
        "route": route,
        "handler": handler,
        "intent": intent,
        "confidence": confidence,
        "reason_codes": reason_codes,
        **extra,
    }


def _build_decision(
    chosen: dict[str, Any],
    *,
    candidates: list[dict[str, Any]],
    reason: str,
    fallback_route: RouteKind | None = None,
    policy_flags: dict[str, Any] | None = None,
    used_llm: bool = False,
    router_mode: str = "rules",
    timing_ms: float = 0.0,
) -> RouteDecision:
    return RouteDecision(
        route=chosen["route"],
        handler=chosen["handler"],
        intent=chosen["intent"],
        confidence=float(chosen["confidence"]),
        reason=reason,
        reason_codes=list(chosen.get("reason_codes") or []),
        requires_clarification=bool(chosen.get("requires_clarification")),
        fallback_route=fallback_route,
        candidate_routes=candidates,
        policy_flags=policy_flags or {},
        timing_ms=timing_ms,
        used_llm=used_llm,
        router_mode=router_mode,
        list_scope=chosen.get("list_scope"),
    )


def _shell_prefix(message: str) -> bool:
    lowered = message.lower().strip()
    for prefix in ("run ", "exec ", "shell ", "wykonaj ", "uruchom "):
        if lowered.startswith(prefix):
            return True
    return bool(re.match(r"^(echo|ls|cat|git|python|npm)\s", message.strip(), re.I))


def decide_route_rules(
    message: str,
    *,
    chat_mode: str = "discuss",
    use_rag: bool = True,
    policy_flags: dict[str, Any] | None = None,
) -> RouteDecision:
    """Kaskada reguł z listą kandydatów (ranking confidence)."""
    text = (message or "").strip()
    flags = _router_flags(chat_mode, use_rag, policy_flags)

    if not text:
        return _empty_route_decision(flags)

    routed = (
        _mode_route_decision(chat_mode, flags)
        or _file_list_route_decision(text, flags)
        or _shell_route_decision(text, flags)
    )
    if routed:
        return routed

    if chat_mode == "discuss":
        return _default_discuss_decision(flags)
    return _fallback_mode_decision(chat_mode, flags)


def _router_flags(
    chat_mode: str,
    use_rag: bool,
    policy_flags: dict[str, Any] | None,
) -> dict[str, Any]:
    flags = dict(policy_flags or {})
    flags.setdefault("chat_mode", chat_mode)
    flags.setdefault("use_rag", use_rag)
    return flags


def _empty_route_decision(flags: dict[str, Any]) -> RouteDecision:
    chosen = _candidate("unknown", "none", "empty", 0.0, ["empty_message"])
    return _build_decision(
        chosen,
        candidates=[chosen],
        reason="Pusta wiadomość",
        policy_flags=flags,
    )


def _mode_route_decision(
    chat_mode: str,
    flags: dict[str, Any],
) -> RouteDecision | None:
    if chat_mode == "search_context":
        chosen = _candidate(
            "rag",
            "chat.handle_message.rag",
            "rag_query",
            0.95,
            ["mode_search_context"],
        )
        return _build_decision(
            chosen,
            candidates=[chosen],
            reason="Tryb czatu wymusza RAG",
            fallback_route="nlp2dsl",
            policy_flags=flags,
        )
    if chat_mode == "run_task":
        chosen = _candidate(
            "mullm_shell",
            "workspace.create_task_immediate",
            "shell_task",
            0.95,
            ["mode_run_task"],
        )
        return _build_decision(
            chosen,
            candidates=[chosen],
            reason="Tryb Shell — ticket od razu",
            policy_flags=flags,
        )
    return None


def _file_list_route_decision(
    text: str,
    flags: dict[str, Any],
) -> RouteDecision | None:
    if not chat_service.is_file_list_intent(text):
        return None
    scope = chat_service.file_list_scope(text)
    chosen = _candidate(
        "mullm_file_list",
        "conductor._mullm_file_list_turn",
        "file_list",
        0.92,
        ["intent_file_list", f"scope_{scope}"],
        list_scope=scope,
    )
    fallback = _candidate(
        "nlp2dsl",
        "nlp2dsl.workflow.chat",
        "workflow",
        0.35,
        ["fallback_nlp2dsl"],
    )
    return _build_decision(
        chosen,
        candidates=[chosen, fallback],
        reason=f"Lista plików (scope={scope})",
        fallback_route="nlp2dsl",
        policy_flags=flags,
    )


def _shell_route_decision(
    text: str,
    flags: dict[str, Any],
) -> RouteDecision | None:
    if not _shell_prefix(text):
        return None
    chosen = _candidate(
        "mullm_shell",
        "workspace.create_task_immediate",
        "shell_inline",
        0.88,
        ["shell_prefix"],
    )
    return _build_decision(
        chosen,
        candidates=[chosen],
        reason="Wykryto polecenie shell w tekście",
        fallback_route="nlp2dsl",
        policy_flags=flags,
    )


def _default_discuss_decision(flags: dict[str, Any]) -> RouteDecision:
    nlp_c = _candidate(
        "nlp2dsl",
        "nlp2dsl.workflow.chat",
        "workflow_dsl",
        0.6,
        ["default_discuss", "delegate_nlp2dsl"],
    )
    rag_c = _candidate(
        "rag",
        "chat.handle_message.rag",
        "rag_fallback",
        0.45,
        ["fallback_if_nlp_down"],
    )
    return _build_decision(
        nlp_c,
        candidates=[nlp_c, rag_c],
        reason="Domyślny discuss → nlp2dsl (workflow); RAG gdy nlp2dsl niedostępny",
        fallback_route="rag",
        policy_flags=flags,
    )


def _fallback_mode_decision(chat_mode: str, flags: dict[str, Any]) -> RouteDecision:
    chosen = _candidate(
        "rag",
        "chat.handle_message.rag",
        "rag_mode",
        0.5,
        [f"mode_{chat_mode}"],
    )
    return _build_decision(
        chosen,
        candidates=[chosen],
        reason=f"Fallback dla trybu {chat_mode}",
        policy_flags=flags,
    )


async def decide_route_llm(message: str) -> RouteDecision | None:
    """Opcjonalna klasyfikacja JSON przez OpenRouter."""
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return None
    model = os.getenv("LLM_MODEL", "openrouter/openai/gpt-5-mini")
    try:
        data = await _llm_classifier_data(api_key, model, message)
        return _llm_decision_from_data(data) if data else None
    except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError):
        return None


async def _llm_classifier_data(
    api_key: str,
    model: str,
    message: str,
) -> dict[str, Any] | None:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=_llm_classifier_payload(model, message),
        )
        if response.status_code != 200:
            return None
        return _extract_llm_json(response.json()["choices"][0]["message"]["content"])


def _llm_classifier_payload(model: str, message: str) -> dict[str, Any]:
    return {
        "model": _normalize_router_model(model),
        "messages": [
            {"role": "system", "content": _llm_system_prompt()},
            {"role": "user", "content": message},
        ],
        "temperature": 0,
        "max_tokens": 160,
    }


def _llm_system_prompt() -> str:
    return (
        "Klasyfikuj intencję użytkownika Mullm. Odpowiedz TYLKO JSON:\n"
        '{"route":"mullm_file_list|mullm_shell|nlp2dsl|rag|unknown",'
        '"intent":"short_slug","confidence":0.0-1.0,'
        '"list_scope":"all|user|system|session|rag|null",'
        '"reason_codes":["code1"]}'
    )


def _normalize_router_model(model: str) -> str:
    return model.replace("openrouter/", "", 1) if model.startswith("openrouter/") else model


def _extract_llm_json(content: str) -> dict[str, Any] | None:
    match = re.search(r"\{[^{}]+\}", content, re.DOTALL)
    return json.loads(match.group()) if match else None


def _llm_decision_from_data(data: dict[str, Any]) -> RouteDecision:
    route = _llm_route(data.get("route", "unknown"))
    chosen = _candidate(
        route,  # type: ignore[arg-type]
        _LLM_HANDLERS[route],
        data.get("intent") or route,
        float(data.get("confidence", 0.7)),
        list(data.get("reason_codes") or ["llm_classifier"]),
        list_scope=data.get("list_scope") or None,
    )
    return _build_decision(
        chosen,
        candidates=[chosen],
        reason="OpenRouter classifier",
        used_llm=True,
        router_mode="llm",
    )


def _llm_route(route: str) -> str:
    return route if route in _LLM_HANDLERS else "unknown"


async def decide_route(
    message: str,
    *,
    chat_mode: str = "discuss",
    use_rag: bool = True,
    policy_flags: dict[str, Any] | None = None,
) -> RouteDecision:
    t0 = time.perf_counter()
    router_mode = (os.getenv("PROMPT_ROUTER_MODE", "rules") or "rules").lower().strip()
    rules = decide_route_rules(
        message,
        chat_mode=chat_mode,
        use_rag=use_rag,
        policy_flags=policy_flags,
    )
    decision = rules
    if router_mode == "llm":
        llm = await decide_route_llm(message)
        decision = _merged_llm_decision(rules, llm)
    decision.timing_ms = (time.perf_counter() - t0) * 1000
    decision.router_mode = router_mode if not decision.used_llm else "llm"
    return decision


def _merged_llm_decision(
    rules: RouteDecision,
    llm: RouteDecision | None,
) -> RouteDecision:
    if llm and llm.confidence > rules.confidence:
        llm.candidate_routes = rules.candidate_routes + [
            candidate
            for candidate in llm.candidate_routes
            if candidate not in rules.candidate_routes
        ]
        llm.fallback_route = rules.route
        llm.policy_flags = {**rules.policy_flags, **llm.policy_flags}
        return llm
    rules.policy_flags["llm_skipped"] = True
    if llm:
        rules.candidate_routes.append(
            {
                "route": llm.route,
                "confidence": llm.confidence,
                "reason_codes": ["llm_lower_confidence"],
            }
        )
    return rules


def record_route_event(
    session_id: str,
    decision: RouteDecision,
    *,
    event_type: str = "RouteDecided",
    outcome: str = "applied",
) -> None:
    """Zapis do ledger sesji (observability)."""
    from app.workspace import get_or_create

    session = get_or_create(session_id)
    session.add_event(
        event_type,
        f"{decision.route} → {decision.handler} ({outcome})",
        routing=decision.to_dict(),
        outcome=outcome,
    )
