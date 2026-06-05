"""
Jawny router promptu użytkownika → handler Mullm / nlp2dsl / RAG.

Lokalnie (równolegle): reguły + user_expectations (YAML) + nlp2cmd.
OpenRouter tylko gdy lokalna analiza nie ma wystarczającej confidence.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Literal

import httpx

from app import chat as chat_service
from app.agent_plugins.registry import analyze_shell_nl
from app.agent_plugins.protocol import ShellTranslation
from app.routing_schemas import (
    NlpCommandAnalysis,
    llm_system_prompt_with_schema,
    parse_llm_classifier,
)

RouteKind = Literal[
    "mullm_file_list",
    "mullm_shell",
    "nlp2cmd_shell",
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
    "nlp2cmd_shell": "workspace.create_task_immediate",
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


_HOST_LIST_CMD = re.compile(
    r"\b(ls|find|tree|du)\b.*(~|/home|\$HOME)|"
    r"^ls\b|"
    r"\bls\s+.*-",
    re.IGNORECASE,
)
_REGISTRY_LIST_HINTS = (
    "rejestr",
    "access fabric",
    "wgrane",
    "localfs",
    "w workspace",
    "indeks rag",
    "nie shell",
)
_HOST_FILESYSTEM_HINTS = (
    "na linux",
    "linuxie",
    "na hoście",
    "na hoscie",
    "hosta",
    "katalog domow",
    "katalogu domowym",
    "home directory",
    "folder domow",
    "folder usera na",
    "systemowego usera",
    "/home/",
    " na ~",
)
_LOCAL_EXECUTABLE_ROUTES = frozenset(
    {"mullm_file_list", "mullm_shell", "nlp2cmd_shell", "rag"}
)
_LOCAL_SOURCE_PRIORITY = {"nlp2cmd": 0, "expectations": 1, "rules": 2}


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

    routed = _direct_route_decision(chat_mode, text, flags)
    if routed:
        return routed

    return _default_route_decision(chat_mode, flags)


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


def _direct_route_decision(
    chat_mode: str,
    text: str,
    flags: dict[str, Any],
) -> RouteDecision | None:
    resolvers = (
        lambda: _mode_route_decision(chat_mode, flags),
        lambda: _file_list_route_decision(text, flags),
        lambda: _shell_route_decision(text, flags),
        lambda: _shell_nl_route_decision(text, flags),
    )
    for resolver in resolvers:
        decision = resolver()
        if decision:
            return decision
    return None


def _default_route_decision(chat_mode: str, flags: dict[str, Any]) -> RouteDecision:
    if chat_mode == "discuss":
        return _default_discuss_decision(flags)
    return _fallback_mode_decision(chat_mode, flags)


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


# @intract.v1 id:mullm.route.file_list.decide scope:function intent:route:file_list domain:routing forbid:shell validate:return_value meaning:"Router: mullm_file_list nie mullm_shell"
def _file_list_route_decision(
    text: str,
    flags: dict[str, Any],
) -> RouteDecision | None:
    if not chat_service.is_file_list_intent(text):
        return None
    scope = chat_service.file_list_scope(text)
    conf = 0.92
    if (
        scope == "user"
        and not _registry_scope_requested(text)
        and not _explicit_registry_list(text)
    ):
        # Bez jawnego rejestru — nlp2cmd (ls ~) może wygrać równoległą analizę lokalną.
        conf = 0.78
    chosen = _candidate(
        "mullm_file_list",
        "conductor._mullm_file_list_turn",
        "file_list",
        conf,
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


# @intract.v1 id:mullm.route.shell_prefix.decide scope:function intent:route:shell_prefix domain:routing validate:return_value meaning:"Jawny prefix run/exec → mullm_shell"
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


def _shell_nl_route_decision(
    text: str,
    flags: dict[str, Any],
) -> RouteDecision | None:
    if not chat_service.is_shell_nl_intent(text):
        return None
    chosen = _candidate(
        "nlp2cmd_shell",
        "workspace.create_task_immediate",
        "shell_nlp2cmd",
        0.82,
        ["ingress_shell_nl", "local_shell_nl"],
    )
    shell_fb = _candidate(
        "mullm_shell",
        "workspace.create_task_immediate",
        "shell_inline",
        0.72,
        ["shell_nl_fallback"],
    )
    return _build_decision(
        chosen,
        candidates=[chosen, shell_fb],
        reason="NL shell (lokalna reguła) → nlp2cmd",
        fallback_route="mullm_shell",
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
        if not data:
            return None
        return _llm_decision_from_data(data)
    except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError, TypeError):
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
        body = response.json()
        choices = body.get("choices") or []
        if not choices:
            return None
        msg = choices[0].get("message") or {}
        content = msg.get("content")
        return _extract_llm_json(content if isinstance(content, str) else None)


def _llm_classifier_payload(model: str, message: str) -> dict[str, Any]:
    return {
        "model": _normalize_router_model(model),
        "messages": [
            {"role": "system", "content": llm_system_prompt_with_schema()},
            {"role": "user", "content": message},
        ],
        "temperature": 0,
        "max_tokens": 160,
    }


def _normalize_router_model(model: str) -> str:
    return model.replace("openrouter/", "", 1) if model.startswith("openrouter/") else model


def _extract_llm_json(content: str | None) -> dict[str, Any] | None:
    if not content:
        return None
    match = re.search(r"\{[^{}]+\}", content, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


def _llm_decision_from_data(data: dict[str, Any]) -> RouteDecision | None:
    parsed = parse_llm_classifier(data)
    if not parsed:
        return None
    route = _llm_route(parsed.route)
    chosen = _candidate(
        route,  # type: ignore[arg-type]
        _LLM_HANDLERS[route],
        parsed.intent,
        parsed.confidence,
        list(parsed.reason_codes) or ["llm_classifier"],
        list_scope=parsed.list_scope,
    )
    return _build_decision(
        chosen,
        candidates=[chosen],
        reason="OpenRouter classifier",
        used_llm=True,
        router_mode="llm",
        policy_flags={
            "llm_classifier_schema": parsed.schema_id,
            "llm_classifier": parsed.model_dump(mode="json"),
        },
    )


def _llm_route(route: str) -> str:
    return route if route in _LLM_HANDLERS else "unknown"


def _explicit_registry_list(message: str) -> bool:
    lowered = (message or "").lower()
    return any(hint in lowered for hint in _REGISTRY_LIST_HINTS)


def _registry_scope_requested(message: str) -> bool:
    lowered = (message or "").lower()
    return _explicit_registry_list(message) or "w scope" in lowered


def _host_filesystem_list_requested(message: str) -> bool:
    lowered = (message or "").lower()
    return any(hint in lowered for hint in _HOST_FILESYSTEM_HINTS) or "~" in lowered


def _command_looks_like_host_list(command: str) -> bool:
    cmd = (command or "").strip()
    if not cmd:
        return False
    return bool(_HOST_LIST_CMD.search(cmd))


def _nlp2cmd_min_confidence() -> float:
    try:
        return float(os.getenv("MULLM_ROUTING_NLP2CMD_MIN_CONFIDENCE", "0.65"))
    except ValueError:
        return 0.65


def _routing_use_nlp2cmd() -> bool:
    return os.getenv("MULLM_ROUTING_NLP2CMD", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _local_min_confidence() -> float:
    try:
        return float(os.getenv("MULLM_ROUTING_LOCAL_MIN_CONFIDENCE", "0.80"))
    except ValueError:
        return 0.80


def _local_confidence_sufficient(decision: RouteDecision) -> bool:
    if decision.route in _LOCAL_EXECUTABLE_ROUTES:
        return decision.confidence >= _local_min_confidence()
    if decision.route == "nlp2dsl":
        return decision.confidence >= 0.55
    return decision.confidence >= 0.85 and decision.route != "unknown"


def _match_expectations_local(message: str) -> list[dict[str, Any]]:
    from app.routing_policy import load_policy
    from app.routing_trace import match_user_expectations

    policy = load_policy()
    return match_user_expectations(message, policy)


def _decision_from_expectations(
    message: str,
    expectations: list[dict[str, Any]],
    rules: RouteDecision,
) -> RouteDecision | None:
    if not expectations:
        return None
    spec = expectations[0]
    route = str(spec.get("route") or "")
    if route not in _LLM_HANDLERS:
        return None
    reason_codes = list(spec.get("reason_codes") or ["expectation_yaml"])
    chosen = _candidate(
        route,  # type: ignore[arg-type]
        _LLM_HANDLERS[route],
        f"expectation_{spec.get('id', 'yaml')}",
        0.86,
        reason_codes,
    )
    return _build_decision(
        chosen,
        candidates=[chosen, *rules.candidate_routes[:1]],
        reason=f"user_expectations: {spec.get('id', 'match')}",
        fallback_route=rules.route,
        policy_flags={
            **rules.policy_flags,
            "expectation_id": spec.get("id"),
            "expectation_standard": spec.get("standard", ""),
        },
        router_mode="local",
    )


async def _safe_analyze_shell_nl(message: str) -> NlpCommandAnalysis | None:
    if not _routing_use_nlp2cmd():
        return None
    try:
        return await analyze_shell_nl(message)
    except Exception:
        return None


async def _gather_local_analyses(
    message: str,
    *,
    chat_mode: str = "discuss",
    use_rag: bool = True,
    policy_flags: dict[str, Any] | None = None,
) -> tuple[RouteDecision, NlpCommandAnalysis | None, list[dict[str, Any]]]:
    expectations = _match_expectations_local(message)
    rules, analysis = await asyncio.gather(
        asyncio.to_thread(
            decide_route_rules,
            message,
            chat_mode=chat_mode,
            use_rag=use_rag,
            policy_flags=policy_flags,
        ),
        _safe_analyze_shell_nl(message),
    )
    return rules, analysis, expectations


def _pick_local_winner(
    pool: list[tuple[RouteDecision, str]],
) -> tuple[RouteDecision, str]:
    return min(
        pool,
        key=lambda item: (
            -item[0].confidence,
            _LOCAL_SOURCE_PRIORITY.get(item[1], 9),
        ),
    )


def _resolve_local_decision(
    message: str,
    *,
    rules: RouteDecision,
    analysis: NlpCommandAnalysis | None,
    expectations: list[dict[str, Any]],
) -> RouteDecision:
    pool: list[tuple[RouteDecision, str]] = [(rules, "rules")]

    exp_dec = _decision_from_expectations(message, expectations, rules)
    if exp_dec:
        pool.append((exp_dec, "expectations"))

    nlp_dec: RouteDecision | None = None
    if analysis:
        translation = analysis.to_shell_translation()
        if _should_prefer_nlp2cmd_over_rules(message, translation, rules):
            nlp_dec = _decision_from_nlp2cmd(
                message,
                translation,
                rules=rules,
                analysis=analysis,
            )
            pool.append((nlp_dec, "nlp2cmd"))

    winner, source = _pick_local_winner(pool)
    flags: dict[str, Any] = {
        **winner.policy_flags,
        "local_analysis_parallel": True,
        "local_winner": source,
        "local_candidates": [
            {"source": src, "route": d.route, "confidence": d.confidence}
            for d, src in pool
        ],
    }
    if nlp_dec is None:
        flags["routing_nlp2cmd_skipped"] = True if analysis is None else "blocked_or_low_conf"
    winner.policy_flags = flags
    winner.router_mode = "local"
    return winner


def _decision_from_nlp2cmd(
    message: str,
    translation: ShellTranslation,
    *,
    rules: RouteDecision,
    analysis: NlpCommandAnalysis | None = None,
) -> RouteDecision:
    nlp_c = _candidate(
        "nlp2cmd_shell",
        "workspace.create_task_immediate",
        "shell_nlp2cmd",
        max(0.85, float(translation.confidence or 0.0)),
        ["routing_nlp2cmd", "nlp2cmd_translate"],
    )
    candidates = [nlp_c]
    for c in rules.candidate_routes:
        if c.get("route") != "nlp2cmd_shell":
            candidates.append(c)
    flags: dict[str, Any] = {
        **rules.policy_flags,
        "shell_plugin": "nlp2cmd",
        "routing_nlp2cmd": True,
    }
    if analysis:
        flags.update(analysis.to_policy_flags())
    else:
        flags["nlp2cmd_translation"] = {
            "command": translation.command,
            "confidence": translation.confidence,
            "domain": translation.domain,
            "intent": translation.intent,
        }
    return _build_decision(
        nlp_c,
        candidates=candidates,
        reason=f"nlp2cmd → `{translation.command[:120]}`",
        fallback_route=rules.route,
        policy_flags=flags,
        router_mode="hybrid",
    )


def _should_prefer_nlp2cmd_over_rules(
    message: str,
    translation: ShellTranslation,
    rules: RouteDecision,
) -> bool:
    if (translation.confidence or 0.0) < _nlp2cmd_min_confidence():
        return False
    cmd = (translation.command or "").strip()
    if not cmd:
        return False
    if _explicit_registry_list(message):
        return False
    if rules.route == "mullm_file_list":
        if not chat_service.is_file_list_intent(message):
            return _command_looks_like_host_list(cmd)
        if _registry_scope_requested(message) or _explicit_registry_list(message):
            return False
        return _command_looks_like_host_list(cmd)
    if rules.route == "mullm_shell" or chat_service.is_nlp2cmd_candidate(message):
        return True
    if _shell_prefix(message):
        return True
    return _command_looks_like_host_list(cmd)


def _resolve_router_mode() -> str:
    raw = (os.getenv("PROMPT_ROUTER_MODE", "auto") or "auto").lower().strip()
    if raw != "auto":
        return raw
    if os.getenv("OPENROUTER_API_KEY", "").strip():
        return "hybrid"
    return "hybrid" if _routing_use_nlp2cmd() else "rules"


async def decide_route_local_first(
    message: str,
    *,
    chat_mode: str = "discuss",
    use_rag: bool = True,
    policy_flags: dict[str, Any] | None = None,
) -> RouteDecision:
    """Równolegle: reguły + expectations + nlp2cmd; OpenRouter tylko jako fallback."""
    rules, analysis, expectations = await _gather_local_analyses(
        message,
        chat_mode=chat_mode,
        use_rag=use_rag,
        policy_flags=policy_flags,
    )
    decision = _resolve_local_decision(
        message,
        rules=rules,
        analysis=analysis,
        expectations=expectations,
    )

    if _local_confidence_sufficient(decision):
        decision.policy_flags["routing_llm_skipped"] = "local_sufficient"
        return decision

    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        decision.policy_flags["routing_llm_skipped"] = "no_api_key"
        return decision

    llm = await decide_route_llm(message)
    if not llm:
        decision.policy_flags["routing_llm_skipped"] = "llm_unavailable"
        return decision

    if llm.confidence > decision.confidence and llm.route in _LLM_HANDLERS:
        llm.candidate_routes = decision.candidate_routes + [
            c for c in llm.candidate_routes if c not in decision.candidate_routes
        ]
        llm.fallback_route = decision.route
        llm.policy_flags = {
            **decision.policy_flags,
            **llm.policy_flags,
            "routing_llm_skipped": False,
            "local_fallback_route": decision.route,
        }
        return llm

    decision.policy_flags["routing_llm_skipped"] = "llm_lower_confidence"
    decision.candidate_routes.append(
        {
            "route": llm.route,
            "confidence": llm.confidence,
            "reason_codes": ["llm_lower_confidence"],
        }
    )
    return decision


async def decide_route_hybrid(
    message: str,
    *,
    chat_mode: str = "discuss",
    use_rag: bool = True,
    policy_flags: dict[str, Any] | None = None,
) -> RouteDecision:
    return await decide_route_local_first(
        message,
        chat_mode=chat_mode,
        use_rag=use_rag,
        policy_flags=policy_flags,
    )


async def decide_route(
    message: str,
    *,
    chat_mode: str = "discuss",
    use_rag: bool = True,
    policy_flags: dict[str, Any] | None = None,
) -> RouteDecision:
    t0 = time.perf_counter()
    router_mode = _resolve_router_mode()
    if router_mode == "hybrid":
        decision = await decide_route_hybrid(
            message,
            chat_mode=chat_mode,
            use_rag=use_rag,
            policy_flags=policy_flags,
        )
        decision.router_mode = (
            "hybrid+llm" if decision.used_llm else ("hybrid" if decision.router_mode == "local" else decision.router_mode)
        )
    elif router_mode == "llm":
        decision = await decide_route_local_first(
            message,
            chat_mode=chat_mode,
            use_rag=use_rag,
            policy_flags=policy_flags,
        )
        decision.router_mode = "llm" if decision.used_llm else "local"
    else:
        decision = decide_route_rules(
            message,
            chat_mode=chat_mode,
            use_rag=use_rag,
            policy_flags=policy_flags,
        )
        decision.router_mode = "rules"
    decision.timing_ms = (time.perf_counter() - t0) * 1000
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
    rules.policy_flags["routing_llm_skipped"] = "local_preferred"
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
