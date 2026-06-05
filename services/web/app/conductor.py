from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app import chat as chat_service
from app import nlp2dsl_bridge as nlp
from app import prompt_router
from app import routing_policy
from app import routing_feedback
from app import routing_trace
from app.routing.execution_resolver import route_from_orientation
from app.routing.orientation_provider import orient_message
from app.agent_plugins import translate_shell_nl
from app.agent_plugins.protocol import ShellTranslation
from app.workspace import get_or_create


@dataclass
class TurnState:
    session_id: str
    message: str
    nlp_conversation_id: str | None
    scope_files: list[str] | None
    scope_uris: list[str] | None
    wait_for_confirmation: bool
    chat_mode: str
    use_rag: bool
    policy: routing_policy.RoutingPolicy
    pipeline_ctx: dict[str, Any]
    decision: prompt_router.RouteDecision | None = None


def _merge_nlp2dsl_routing(
    out: dict[str, Any],
    nlp_routing: dict[str, Any] | None,
    decision: prompt_router.RouteDecision | None = None,
) -> None:
    if not nlp_routing:
        return
    out["nlp2dsl_routing"] = nlp_routing
    if decision is not None:
        nlp.merge_intent_into_policy_flags(decision.policy_flags, nlp_routing)


def _attach_routing(
    session_id: str,
    out: dict[str, Any],
    decision: prompt_router.RouteDecision,
) -> dict[str, Any]:
    routing = decision.to_dict()
    orient = decision.policy_flags.get("nlp2dsl_orientation")
    if orient:
        routing["nlp2dsl"] = orient
        routing["nlp2dsl_orient"] = True
        routing["nlp2dsl_invoked"] = True
        src = decision.policy_flags.get("orientation_source") or orient.get("source")
        if src:
            routing["orientation_source"] = src
    shell_trans = decision.policy_flags.get("shell_translation_source")
    if shell_trans:
        routing["shell_translation_source"] = shell_trans
    elif out.get("nlp2dsl_routing"):
        routing["nlp2dsl"] = out["nlp2dsl_routing"]
        routing["nlp2dsl_invoked"] = True
    elif decision.route in ("mullm_file_list", "mullm_shell", "nlp2cmd_shell"):
        routing["nlp2dsl_skipped"] = True
    shell_plugin = decision.policy_flags.get("shell_plugin")
    if shell_plugin:
        routing["shell_plugin"] = shell_plugin
    if shell_plugin == "nlp2cmd":
        trans = decision.policy_flags.get("nlp2cmd_translation")
        if isinstance(trans, dict):
            routing["nlp2cmd"] = trans
    elif shell_plugin == "nlp2dsl_orient":
        trans = decision.policy_flags.get("nlp2cmd_translation")
        if isinstance(trans, dict):
            routing["nlp2dsl_orient_cmd"] = trans
    routing["turn_id"] = routing_feedback.new_turn_id()
    out["routing"] = routing
    chat_service.stamp_last_assistant_routing(session_id, routing)
    return out


def _enrich_decision(
    decision: prompt_router.RouteDecision,
    session_id: str,
    *,
    chat_mode: str,
    pipeline_ctx: dict[str, Any],
) -> prompt_router.RouteDecision:
    policy = routing_policy.load_policy()
    session = get_or_create(session_id)
    order = policy.ingress_for_mode(chat_mode)
    decision.policy_flags["ingress_order"] = order
    decision.policy_flags["assigned_agent"] = policy.agent_for_route(
        decision.route,
        session_agent_id=session.context.agent_id or None,
    )
    hits = pipeline_ctx.get("rag_probe_hits")
    if hits:
        decision.policy_flags["rag_probe_hits"] = hits
        decision.reason_codes = list(decision.reason_codes) + ["rag_probe_hit"]
    return decision


async def _rag_answer_turn(
    *,
    session_id: str,
    message: str,
    scope_files: list[str] | None,
    scope_uris: list[str] | None,
) -> dict[str, Any]:
    return await chat_service.handle_message(
        session_id=session_id,
        message=message,
        use_rag=True,
        scope_files=scope_files,
        scope_uris=scope_uris,
    )


async def _execute_rules_route(
    *,
    session_id: str,
    message: str,
    decision: prompt_router.RouteDecision,
    nlp_conversation_id: str | None,
    scope_files: list[str] | None,
    scope_uris: list[str] | None,
    wait_for_confirmation: bool,
) -> dict[str, Any] | None:
    """Wykonuje trasę z reguł (file_list / shell) lub None → dalszy pipeline."""
    handler = _RULE_ROUTE_HANDLERS.get(decision.route)
    if not handler:
        return None
    return await handler(
        session_id=session_id,
        message=message,
        decision=decision,
        scope_files=scope_files,
        scope_uris=scope_uris,
        wait_for_confirmation=wait_for_confirmation,
    )


async def _execute_file_list_route(
    *,
    session_id: str,
    message: str,
    decision: prompt_router.RouteDecision,
    scope_files: list[str] | None,
    scope_uris: list[str] | None,
    wait_for_confirmation: bool,
) -> dict[str, Any]:
    out = await _mullm_file_list_turn(
        session_id=session_id,
        message=message,
        scope_files=scope_files,
        scope_uris=scope_uris,
    )
    prompt_router.record_route_event(session_id, decision, outcome="succeeded")
    return _attach_routing(session_id, out, decision)


async def _execute_shell_route(
    *,
    session_id: str,
    message: str,
    decision: prompt_router.RouteDecision,
    scope_files: list[str] | None,
    scope_uris: list[str] | None,
    wait_for_confirmation: bool,
) -> dict[str, Any]:
    shell = _extract_shell(message)
    translation: ShellTranslation | None = _translation_from_policy_flags(decision)
    if not shell and translation:
        shell = translation.command
        if decision.route != "nlp2cmd_shell":
            decision = _apply_nlp2cmd_decision(decision, translation)
    if not shell:
        translation = translation or await translate_shell_nl(message)
        if translation:
            shell = translation.command
            decision = _apply_nlp2cmd_decision(decision, translation)
    if not shell:
        session = get_or_create(session_id)
        return await _missing_shell_response(
            session_id,
            decision,
            message=message,
            nlp_conversation_id=session.nlp2dsl_conversation_id,
            scope_files=scope_files,
            scope_uris=scope_uris,
            wait_for_confirmation=wait_for_confirmation,
        )
    result = await _create_shell_task(
        session_id,
        message=message,
        shell=shell,
        wait_for_confirmation=wait_for_confirmation,
        agent=decision.policy_flags.get("assigned_agent"),
    )
    return _shell_route_response(
        session_id,
        message,
        decision,
        result,
        translation=translation,
        wait_for_confirmation=wait_for_confirmation,
    )


async def _missing_shell_response(
    session_id: str,
    decision: prompt_router.RouteDecision,
    *,
    message: str = "",
    nlp_conversation_id: str | None = None,
    scope_files: list[str] | None = None,
    scope_uris: list[str] | None = None,
    wait_for_confirmation: bool = False,
) -> dict[str, Any]:
    """Brak polecenia shell — spróbuj nlp2dsl (dopytania) zamiast sztywnego komunikatu."""
    if await nlp.health():
        try:
            out = await _nlp2dsl_turn(
                session_id=session_id,
                message=message or "Potrzebuję doprecyzowania polecenia.",
                nlp_conversation_id=nlp_conversation_id,
                scope_files=scope_files,
                scope_uris=scope_uris,
                wait_for_confirmation=wait_for_confirmation,
            )
            decision.route = "nlp2dsl"
            decision.handler = "nlp2dsl.workflow.chat"
            decision.reason = "Brak shell — delegacja do nlp2dsl (dopytania)"
            decision.reason_codes = list(decision.reason_codes) + ["nlp2dsl_clarify_fallback"]
            decision.requires_clarification = True
            _merge_nlp2dsl_routing(out, out.get("nlp2dsl_routing"), decision)
            prompt_router.record_route_event(session_id, decision, outcome="clarify")
            return _attach_routing(session_id, out, decision)
        except Exception:
            pass
    decision.requires_clarification = True
    prompt_router.record_route_event(
        session_id, decision, event_type="RouteFailed", outcome="no_shell"
    )
    out = {
        "reply": "Podaj polecenie shell (np. `run ls -la`) lub opisz workflow (np. faktura).",
        "history": chat_service.get_history(session_id),
    }
    return _attach_routing(session_id, out, decision)


def _shell_wait_seconds() -> float:
    import os

    raw = (os.getenv("MULLM_SHELL_WAIT_SECONDS") or "20").strip()
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 20.0


async def _create_shell_task(
    session_id: str,
    *,
    message: str,
    shell: str,
    wait_for_confirmation: bool,
    agent: str | None,
) -> dict[str, Any]:
    from app import workspace as ws

    # executor w polityce (shell_agent) ≠ ID agenta NATS — auto_assign wybiera shell-agent-a/b
    result = await ws.create_task_immediate(
        session_id,
        title=message[:80],
        description=message,
        shell_command=shell,
        wait_for_confirmation=wait_for_confirmation,
        agent_id=None,
    )
    result["executor_label"] = agent
    wait_sec = _shell_wait_seconds()
    tid = result.get("task_id")
    if (
        wait_sec > 0
        and not wait_for_confirmation
        and result.get("ok")
        and tid
    ):
        terminal = await chat_service.wait_for_task_terminal(str(tid), timeout=wait_sec)
        if terminal:
            result["terminal_state"] = terminal
    return result


def _translation_from_policy_flags(
    decision: prompt_router.RouteDecision,
) -> ShellTranslation | None:
    raw = (decision.policy_flags or {}).get("nlp2cmd_translation")
    if not isinstance(raw, dict) or not raw.get("command"):
        return None
    return ShellTranslation(
        command=str(raw["command"]),
        confidence=float(raw.get("confidence") or 0.0),
        domain=str(raw.get("domain") or ""),
        intent=str(raw.get("intent") or ""),
    )


def _apply_nlp2cmd_decision(
    decision: prompt_router.RouteDecision,
    translation: ShellTranslation,
) -> prompt_router.RouteDecision:
    flags = dict(decision.policy_flags)
    flags["shell_plugin"] = "nlp2cmd"
    flags["shell_translation_source"] = "nlp2cmd"
    flags["nlp2cmd_translation"] = {
        "command": translation.command,
        "confidence": translation.confidence,
        "domain": translation.domain,
        "intent": translation.intent,
    }
    return prompt_router.RouteDecision(
        route="nlp2cmd_shell",
        handler="workspace.create_task_immediate",
        intent="shell_nlp2cmd",
        confidence=max(decision.confidence, translation.confidence or 0.85),
        reason=f"nlp2cmd → `{translation.command[:120]}`",
        reason_codes=list(decision.reason_codes) + ["nlp2cmd_translate"],
        requires_clarification=decision.requires_clarification,
        fallback_route=decision.fallback_route,
        candidate_routes=decision.candidate_routes,
        policy_flags=flags,
        timing_ms=decision.timing_ms,
        used_llm=decision.used_llm,
        router_mode=decision.router_mode,
        list_scope=decision.list_scope,
    )


def _shell_route_response(
    session_id: str,
    message: str,
    decision: prompt_router.RouteDecision,
    result: dict[str, Any],
    *,
    translation: ShellTranslation | None = None,
    wait_for_confirmation: bool = False,
) -> dict[str, Any]:
    agent = result.get("executor_label") or decision.policy_flags.get("assigned_agent")
    reply = _shell_task_reply(
        result,
        agent,
        translation=translation,
        wait_for_confirmation=wait_for_confirmation,
        shell_plugin=decision.policy_flags.get("shell_plugin"),
    )
    chat_service._append(session_id, "user", message)
    chat_service._append(session_id, "assistant", reply)
    executed = "nlp2cmd_shell" if decision.route == "nlp2cmd_shell" else "mullm_shell"
    out = {
        "reply": reply,
        "task": result,
        "executed": executed,
        "assigned_agent": agent,
        "history": chat_service.get_history(session_id),
    }
    prompt_router.record_route_event(session_id, decision, outcome="succeeded")
    return _attach_routing(session_id, out, decision)


def _shell_task_reply(
    result: dict[str, Any],
    agent: str | None,
    *,
    translation: ShellTranslation | None = None,
    wait_for_confirmation: bool = False,
    shell_plugin: str | None = None,
) -> str:
    tid = result.get("task_id", "?")
    if not result.get("ok"):
        base = f"Nie udało się utworzyć ticketu: {result.get('error')}"
    elif wait_for_confirmation:
        base = f"Ticket `{tid}` w kolejce — potwierdź na liście ticketów (◎)."
    else:
        base = f"Ticket `{tid}`" + (f" → `{agent}`" if agent else "") + " — uruchomiono."
        terminal = result.get("terminal_state")
        if isinstance(terminal, dict):
            base += _format_shell_terminal(terminal)
        elif _shell_wait_seconds() > 0:
            base += (
                f"\n\n(Wynik shell nie gotowy w {_shell_wait_seconds():.0f}s — "
                f"sprawdź ticket ◎ lub wyślij kolejną wiadomość z ID `{tid}`.)"
            )
    if translation:
        label = "nlp2dsl orient" if shell_plugin == "nlp2dsl_orient" else "nlp2cmd"
        return f"{label}: `{translation.command}` (conf={translation.confidence:.2f})\n{base}"
    return base


def _format_shell_terminal(state: dict[str, Any]) -> str:
    status = str(state.get("status") or "").lower()
    if status == "failed":
        err = state.get("error") or "błąd wykonania"
        return f"\n\n**Shell — failed**\n{err}"
    raw = state.get("result")
    if not isinstance(raw, dict):
        return "\n\n**Shell — completed** (brak stdout w stanie zadania)"
    stdout = (raw.get("stdout") or "").strip()
    stderr = (raw.get("stderr") or "").strip()
    exit_code = raw.get("exit_code")
    parts = [f"\n\n**Shell — exit {exit_code}**"]
    if stdout:
        parts.append(f"```\n{stdout[:8000]}\n```")
    if stderr:
        parts.append(f"stderr:\n```\n{stderr[:2000]}\n```")
    if not stdout and not stderr:
        parts.append("(puste stdout/stderr)")
    return "\n".join(parts)


async def _execute_rag_route(
    *,
    session_id: str,
    message: str,
    decision: prompt_router.RouteDecision,
    scope_files: list[str] | None,
    scope_uris: list[str] | None,
    wait_for_confirmation: bool,
) -> dict[str, Any]:
    out = await _rag_answer_turn(
        session_id=session_id,
        message=message,
        scope_files=scope_files,
        scope_uris=scope_uris,
    )
    prompt_router.record_route_event(session_id, decision, outcome="succeeded")
    return _attach_routing(session_id, out, decision)


_RULE_ROUTE_HANDLERS = {
    "mullm_file_list": _execute_file_list_route,
    "mullm_shell": _execute_shell_route,
    "nlp2cmd_shell": _execute_shell_route,
    "rag": _execute_rag_route,
}


async def handle_turn(
    *,
    session_id: str,
    message: str,
    nlp_conversation_id: str | None,
    scope_files: list[str] | None = None,
    scope_uris: list[str] | None = None,
    form_values: dict[str, Any] | None = None,
    wait_for_confirmation: bool = False,
    chat_mode: str = "discuss",
    use_rag: bool = True,
) -> dict[str, Any]:
    """
    Pipeline ingress z routing_policy.yaml (rag_probe → rules → agent_shell → nlp2dsl → rag_answer).
    """
    message = _message_with_form_values(message, form_values)
    policy = routing_policy.load_policy()
    state = TurnState(
        session_id=session_id,
        message=message,
        nlp_conversation_id=nlp_conversation_id,
        scope_files=scope_files,
        scope_uris=scope_uris,
        wait_for_confirmation=wait_for_confirmation,
        chat_mode=chat_mode,
        use_rag=use_rag,
        policy=policy,
        pipeline_ctx={"rag_probe_hits": 0},
    )

    pipeline_result = await _run_ingress_pipeline(state)
    if pipeline_result is not None:
        return await _attach_decision_tree(
            pipeline_result,
            session_id=session_id,
            message=message,
            chat_mode=chat_mode,
            use_rag=use_rag,
        )
    fallback = await _fallback_routed_turn(state)
    return await _attach_decision_tree(
        fallback,
        session_id=session_id,
        message=message,
        chat_mode=chat_mode,
        use_rag=use_rag,
    )


def _message_with_form_values(
    message: str,
    form_values: dict[str, Any] | None,
) -> str:
    message = (message or "").strip()
    if not form_values:
        return message
    extra = nlp.form_to_prompt(None, form_values)
    if not extra:
        return message
    return f"{message} {extra}".strip() if message else extra


async def _attach_decision_tree(
    out: dict[str, Any],
    *,
    session_id: str,
    message: str,
    chat_mode: str,
    use_rag: bool,
) -> dict[str, Any]:
    routing = out.get("routing") or {}
    route = routing.get("route")
    if not route:
        return out
    tree = await routing_trace.explain_pipeline(
        message,
        chat_mode=chat_mode,
        use_rag=use_rag,
        session_id=session_id,
    )
    ingress_step = routing.get("policy_flags", {}).get("pipeline_step")
    tree = routing_trace.align_tree_to_route(tree, route, ingress_step=ingress_step)
    routing["decision_tree"] = tree
    if not routing.get("turn_id"):
        routing["turn_id"] = routing_feedback.new_turn_id()
    out["routing"] = routing
    chat_service.stamp_last_assistant_routing(session_id, routing)
    get_or_create(session_id).add_event(
        "RoutingDecisionTree",
        f"route={route}",
        decision_tree=tree,
    )
    return out


def _should_interrupt_nlp2dsl_resume(state: TurnState) -> bool:
    """Nowa intencja file_list / jawny shell — przerwij wznawianie rozmowy workflow."""
    if state.chat_mode != "discuss":
        return True
    if chat_service.is_file_list_intent(state.message):
        return True
    if prompt_router._shell_prefix(state.message):
        return True
    return False


async def _nlp2dsl_orient_step(state: TurnState) -> dict[str, Any] | None:
    """Orientacja zapytania w nlp2dsl przed regułami / nlp2cmd / OpenRouter."""
    orient = await orient_message(
        state.message,
        connector="mullm",
        session_id=state.session_id,
        chat_mode=state.chat_mode,
    )
    orient_dict = orient.to_dict()
    state.pipeline_ctx["nlp2dsl_orient"] = orient_dict
    state.pipeline_ctx["nlp2dsl_orient_source"] = orient.source
    state.pipeline_ctx["orientation"] = orient_dict
    if orient.category in ("unknown", "system_local"):
        return None

    decision = route_from_orientation(orient)
    if not decision:
        return None

    if decision.route == "nlp2dsl":
        state.decision = _enrich_decision(
            decision,
            state.session_id,
            chat_mode=state.chat_mode,
            pipeline_ctx=state.pipeline_ctx,
        )
        return None

    decision.timing_ms = orient.latency_ms
    state.decision = _enrich_decision(
        decision,
        state.session_id,
        chat_mode=state.chat_mode,
        pipeline_ctx=state.pipeline_ctx,
    )
    state.pipeline_ctx["nlp2dsl_orient_handled"] = True
    result = await _execute_rules_route(
        session_id=state.session_id,
        message=state.message,
        decision=state.decision,
        nlp_conversation_id=state.nlp_conversation_id,
        scope_files=state.scope_files,
        scope_uris=state.scope_uris,
        wait_for_confirmation=state.wait_for_confirmation,
    )
    if result is None:
        return None
    _merge_nlp2dsl_routing(
        result,
        {
            "action": orient.suggested_action,
            "intent": orient.category,
            "confidence": orient.confidence,
            "source": "orientation",
            "orientation": orient_dict,
        },
        state.decision,
    )
    return result


async def _nlp2dsl_resume_step(state: TurnState) -> dict[str, Any] | None:
    """
    Wznów rozmowę nlp2dsl (dopytania, formularz) — nie tylko na słowo „kontynuuj”.
    """
    if not state.nlp_conversation_id:
        return None
    if _should_interrupt_nlp2dsl_resume(state):
        return None
    status = get_or_create(state.session_id).nlp2dsl_status
    if status and status not in ("in_progress", "ready"):
        return None
    if not await nlp.health():
        return None
    state.decision = _enrich_decision(
        _nlp2dsl_continue_decision(),
        state.session_id,
        chat_mode=state.chat_mode,
        pipeline_ctx=state.pipeline_ctx,
    )
    state.decision.reason = "Wznowienie rozmowy nlp2dsl (dopytania / brakujące pola)"
    state.decision.reason_codes = list(state.decision.reason_codes) + ["nlp2dsl_resume"]
    out = await _nlp2dsl_turn(
        session_id=state.session_id,
        message=state.message,
        nlp_conversation_id=state.nlp_conversation_id,
        scope_files=state.scope_files,
        scope_uris=state.scope_uris,
        wait_for_confirmation=state.wait_for_confirmation,
    )
    _merge_nlp2dsl_routing(out, out.get("nlp2dsl_routing"), state.decision)
    prompt_router.record_route_event(state.session_id, state.decision, outcome="succeeded")
    return _attach_routing(state.session_id, out, state.decision)


async def _run_ingress_pipeline(state: TurnState) -> dict[str, Any] | None:
    handlers = {
        "nlp2dsl_resume": _nlp2dsl_resume_step,
        "nlp2dsl_orient": _nlp2dsl_orient_step,
        "rag_probe": _rag_probe_step,
        "rules": _rules_step,
        "agent_shell": _agent_shell_step,
        "nlp2dsl": _nlp2dsl_step,
        "rag_answer": _rag_answer_step,
    }
    for step in state.policy.ingress_for_mode(state.chat_mode):
        handler = handlers.get(step)
        if not handler:
            continue
        result = await handler(state)
        if result is not None:
            return result
    return None


async def _rag_probe_step(state: TurnState) -> dict[str, Any] | None:
    if not _rag_probe_enabled(state):
        return None

    probe = await chat_service.probe_rag(
        session_id=state.session_id,
        message=state.message,
        limit=state.policy.rag_probe.search_limit,
    )
    hits = int(probe.get("hits") or 0)
    state.pipeline_ctx["rag_probe_hits"] = hits
    if not _rag_probe_should_answer(state, hits):
        return None

    return await _rag_probe_answer(state)


def _rag_probe_enabled(state: TurnState) -> bool:
    return bool(
        state.use_rag
        and state.policy.rag_probe.enabled
        and not _should_skip_rag_probe(state)
    )


def _rag_probe_should_answer(state: TurnState, hits: int) -> bool:
    return bool(
        hits >= state.policy.rag_probe.min_hits
        and state.policy.rag_probe.answer_on_hit
    )


async def _rag_probe_answer(state: TurnState) -> dict[str, Any]:
    state.decision = _enrich_decision(
        _rag_probe_decision(),
        state.session_id,
        chat_mode=state.chat_mode,
        pipeline_ctx=state.pipeline_ctx,
    )
    prompt_router.record_route_event(state.session_id, state.decision, outcome="rag_probe")
    out = await _rag_answer_turn(
        session_id=state.session_id,
        message=state.message,
        scope_files=state.scope_files,
        scope_uris=state.scope_uris,
    )
    return _attach_routing(state.session_id, out, state.decision)


def _should_skip_rag_probe(state: TurnState) -> bool:
    settings = state.policy.rag_probe
    if settings.skip_file_list_intent and chat_service.is_file_list_intent(state.message):
        return True
    if settings.skip_shell_prefix and prompt_router._shell_prefix(state.message):
        return True
    return bool(chat_service.is_shell_nl_intent(state.message))


def _nlp2dsl_continue_decision() -> prompt_router.RouteDecision:
    return prompt_router.RouteDecision(
        route="nlp2dsl",
        handler="nlp2dsl.workflow.chat",
        intent="workflow_continue",
        confidence=0.88,
        reason="Kontynuacja rozmowy nlp2dsl",
        reason_codes=["intent_continue", "nlp2dsl_resume"],
        router_mode="rules",
    )


def _mullm_continue_clarify_decision() -> prompt_router.RouteDecision:
    return prompt_router.RouteDecision(
        route="workroom_hint",
        handler="conductor._continue_clarify_turn",
        intent="session_continue",
        confidence=0.88,
        reason="Kontynuacja — wymaga doprecyzowania",
        reason_codes=["intent_continue", "clarify_next_step"],
        router_mode="rules",
    )


def _continue_clarify_reply(state: TurnState) -> str:
    session = get_or_create(state.session_id)
    lines = [
        "„Kontynuuj” — doprecyzuj następny krok, np.:",
        "• lista plikow usera",
        "• wyślij fakturę na … PLN do …",
        "• run ls -la",
    ]
    if session.context.linked_ticket_id:
        lines.append(f"• kontekst ticketu: `{session.context.linked_ticket_id}`")
    if not state.nlp_conversation_id:
        lines.append(
            "(Po restarcie serwisu nie ma aktywnej rozmowy nlp2dsl — "
            "podaj konkretną komendę zamiast samego „kontynuuj”.)"
        )
    return "\n".join(lines)


async def _try_continue_turn(state: TurnState) -> dict[str, Any] | None:
    if not chat_service.is_continue_intent(state.message):
        return None

    if state.nlp_conversation_id and await nlp.health():
        state.decision = _enrich_decision(
            _nlp2dsl_continue_decision(),
            state.session_id,
            chat_mode=state.chat_mode,
            pipeline_ctx=state.pipeline_ctx,
        )
        out = await _nlp2dsl_turn(
            session_id=state.session_id,
            message=state.message,
            nlp_conversation_id=state.nlp_conversation_id,
            scope_files=state.scope_files,
            scope_uris=state.scope_uris,
            wait_for_confirmation=state.wait_for_confirmation,
        )
        _merge_nlp2dsl_routing(
            out,
            out.get("nlp2dsl_routing"),
            state.decision,
        )
        prompt_router.record_route_event(
            state.session_id,
            state.decision,
            outcome="succeeded",
        )
        return _attach_routing(state.session_id, out, state.decision)

    state.decision = _enrich_decision(
        _mullm_continue_clarify_decision(),
        state.session_id,
        chat_mode=state.chat_mode,
        pipeline_ctx=state.pipeline_ctx,
    )
    reply = _continue_clarify_reply(state)
    chat_service._append(state.session_id, "user", state.message)
    chat_service._append(state.session_id, "assistant", reply)
    out = {
        "reply": reply,
        "clarify": {"hint": "Podaj konkretną komendę lub kontynuuj ticket w panelu zadań."},
        "history": chat_service.get_history(state.session_id),
        "correlation_id": state.session_id,
        "nlp2dsl_conversation_id": state.nlp_conversation_id,
    }
    prompt_router.record_route_event(
        state.session_id,
        state.decision,
        outcome="clarify",
    )
    return _attach_routing(state.session_id, out, state.decision)


def _rag_probe_decision() -> prompt_router.RouteDecision:
    return prompt_router.RouteDecision(
        route="rag",
        handler="chat.handle_message.rag",
        intent="rag_probe_answer",
        confidence=0.85,
        reason="RAG probe — trafienie w indeksie",
        reason_codes=["rag_probe", "answer_on_hit"],
        router_mode="policy",
    )


async def _rules_step(state: TurnState) -> dict[str, Any] | None:
    if state.pipeline_ctx.get("nlp2dsl_orient_handled"):
        return None
    continued = await _try_continue_turn(state)
    if continued is not None:
        return continued

    state.decision = await prompt_router.decide_route(
        state.message,
        chat_mode=state.chat_mode,
        use_rag=state.use_rag,
        policy_flags={"pipeline_step": "rules"},
    )
    state.decision = _enrich_decision(
        state.decision,
        state.session_id,
        chat_mode=state.chat_mode,
        pipeline_ctx=state.pipeline_ctx,
    )
    return await _execute_rules_route(
        session_id=state.session_id,
        message=state.message,
        decision=state.decision,
        nlp_conversation_id=state.nlp_conversation_id,
        scope_files=state.scope_files,
        scope_uris=state.scope_uris,
        wait_for_confirmation=state.wait_for_confirmation,
    )


def _should_skip_nlp2dsl_step(state: TurnState) -> bool:
    """Reguły / orient / agent_shell już obsłużyły trasę — nie wołaj nlp2dsl ponownie."""
    if state.pipeline_ctx.get("nlp2dsl_orient_handled"):
        return True
    if state.pipeline_ctx.get("agent_shell_handled"):
        return True
    if state.decision and state.decision.route in (
        "mullm_file_list",
        "mullm_shell",
        "nlp2cmd_shell",
    ):
        return True
    if chat_service.is_file_list_intent(state.message):
        return True
    if prompt_router._shell_prefix(state.message):
        return True
    return False


def _nlp2cmd_ingress_decision(
    translation: ShellTranslation,
) -> prompt_router.RouteDecision:
    return prompt_router.RouteDecision(
        route="nlp2cmd_shell",
        handler="workspace.create_task_immediate",
        intent="shell_nlp2cmd",
        confidence=max(0.85, translation.confidence or 0.0),
        reason=f"agent_shell / nlp2cmd → `{translation.command[:120]}`",
        reason_codes=["ingress_agent_shell", "nlp2cmd_translate"],
        policy_flags={
            "shell_plugin": "nlp2cmd",
            "pipeline_step": "agent_shell",
            "nlp2cmd_translation": {
                "command": translation.command,
                "confidence": translation.confidence,
                "domain": translation.domain,
                "intent": translation.intent,
            },
        },
        router_mode="policy",
    )


# @intract.v1 id:mullm.ingress.agent_shell scope:function intent:orchestrate:agent_shell domain:routing effect:network meaning:"Ingress nlp2cmd→ticket shell_agent; Mullm nie wykonuje polecenia"
async def _agent_shell_step(state: TurnState) -> dict[str, Any] | None:
    """NL → shell (nlp2cmd) → ticket shell_agent — Mullm tylko orkiestruje."""
    if not chat_service.is_nlp2cmd_candidate(state.message):
        return None
    translation = await translate_shell_nl(state.message)
    if not translation:
        return None
    state.decision = _enrich_decision(
        _nlp2cmd_ingress_decision(translation),
        state.session_id,
        chat_mode=state.chat_mode,
        pipeline_ctx=state.pipeline_ctx,
    )
    result = await _create_shell_task(
        state.session_id,
        message=state.message,
        shell=translation.command,
        wait_for_confirmation=state.wait_for_confirmation,
        agent=state.decision.policy_flags.get("assigned_agent"),
    )
    state.pipeline_ctx["agent_shell_handled"] = True
    return _shell_route_response(
        state.session_id,
        state.message,
        state.decision,
        result,
        translation=translation,
        wait_for_confirmation=state.wait_for_confirmation,
    )


async def _nlp2dsl_step(state: TurnState) -> dict[str, Any] | None:
    if _should_skip_nlp2dsl_step(state):
        return None
    if state.decision is None:
        state.decision = await _decide_default_route(state)
    if await nlp.health():
        out = await _nlp2dsl_turn(
            session_id=state.session_id,
            message=state.message,
            nlp_conversation_id=state.nlp_conversation_id,
            scope_files=state.scope_files,
            scope_uris=state.scope_uris,
            wait_for_confirmation=state.wait_for_confirmation,
        )
        _merge_nlp2dsl_routing(
            out,
            out.get("nlp2dsl_routing"),
            state.decision,
        )
        prompt_router.record_route_event(state.session_id, state.decision, outcome="succeeded")
        return _attach_routing(state.session_id, out, state.decision)

    prompt_router.record_route_event(
        state.session_id,
        state.decision,
        event_type="RouteFallbackApplied",
        outcome="nlp_down",
    )
    return None


async def _rag_answer_step(state: TurnState) -> dict[str, Any] | None:
    if not state.use_rag:
        return None
    if state.decision is None:
        state.decision = _enrich_decision(
            _rag_pipeline_decision(),
            state.session_id,
            chat_mode=state.chat_mode,
            pipeline_ctx=state.pipeline_ctx,
        )
    out = await _rag_answer_turn(
        session_id=state.session_id,
        message=state.message,
        scope_files=state.scope_files,
        scope_uris=state.scope_uris,
    )
    prompt_router.record_route_event(state.session_id, state.decision, outcome="rag_answer")
    return _attach_routing(state.session_id, out, state.decision)


def _rag_pipeline_decision() -> prompt_router.RouteDecision:
    return prompt_router.RouteDecision(
        route="rag",
        handler="chat.handle_message.rag",
        intent="rag_pipeline",
        confidence=0.5,
        reason="Krok rag_answer w polityce ingress",
        reason_codes=["ingress_rag_answer"],
        router_mode="policy",
    )


async def _fallback_routed_turn(state: TurnState) -> dict[str, Any]:
    if state.decision is None:
        state.decision = await _decide_default_route(state)
    out = await _fallback_turn(
        session_id=state.session_id,
        message=state.message,
        scope_files=state.scope_files,
        scope_uris=state.scope_uris,
    )
    return _attach_routing(state.session_id, out, state.decision)


async def _decide_default_route(state: TurnState) -> prompt_router.RouteDecision:
    decision = await prompt_router.decide_route(
        state.message,
        chat_mode=state.chat_mode,
        use_rag=state.use_rag,
    )
    return _enrich_decision(
        decision,
        state.session_id,
        chat_mode=state.chat_mode,
        pipeline_ctx=state.pipeline_ctx,
    )


async def _nlp2dsl_turn(
    *,
    session_id: str,
    message: str,
    nlp_conversation_id: str | None,
    scope_files: list[str] | None,
    scope_uris: list[str] | None,
    wait_for_confirmation: bool = False,
) -> dict[str, Any]:
    try:
        resp = await _call_nlp2dsl(nlp_conversation_id, message)
    except Exception as exc:
        return await _fallback_turn(
            session_id=session_id,
            message=message,
            scope_files=scope_files,
            scope_uris=scope_uris,
            prefix_note=f"(nlp2dsl niedostępny: {exc})\n\n",
        )

    cid = resp.get("conversation_id") or nlp_conversation_id
    status = resp.get("status") or "in_progress"
    assistant = resp.get("message") or ""
    nlp_routing = resp.get("routing")

    out = await _nlp2dsl_status_turn(
        session_id=session_id,
        message=message,
        cid=cid,
        status=status,
        assistant=assistant,
        resp=resp,
        scope_files=scope_files,
        scope_uris=scope_uris,
        wait_for_confirmation=wait_for_confirmation,
    )

    if nlp_routing:
        out["nlp2dsl_routing"] = nlp_routing
    return out


async def _nlp2dsl_status_turn(
    *,
    session_id: str,
    message: str,
    cid: str | None,
    status: str,
    assistant: str,
    resp: dict[str, Any],
    scope_files: list[str] | None,
    scope_uris: list[str] | None,
    wait_for_confirmation: bool,
) -> dict[str, Any]:
    if status == "in_progress":
        return _in_progress_turn(session_id, message, resp, cid, status, assistant)
    if status == "ready":
        return await _ready_turn(
            session_id=session_id,
            message=message,
            cid=cid,
            status=status,
            assistant=assistant,
            resp=resp,
            scope_files=scope_files,
            scope_uris=scope_uris,
            wait_for_confirmation=wait_for_confirmation,
        )
    return _closed_turn(session_id, message, cid, status, assistant)


async def _call_nlp2dsl(
    nlp_conversation_id: str | None,
    message: str,
) -> dict[str, Any]:
    if nlp_conversation_id:
        return await nlp.chat_message(nlp_conversation_id, message)
    return await nlp.chat_start(message)


def _nlp_output_base(cid: str | None, status: str) -> dict[str, Any]:
    return {
        "nlp2dsl_conversation_id": cid,
        "nlp2dsl_status": status,
        "clarify": None,
        "task": None,
    }


def _in_progress_turn(
    session_id: str,
    message: str,
    resp: dict[str, Any],
    cid: str | None,
    status: str,
    assistant: str,
) -> dict[str, Any]:
    out = _nlp_output_base(cid, status)
    out["reply"] = assistant or "Potrzebuję jeszcze kilku informacji — uzupełnij poniżej."
    out["clarify"] = {
        "conversation_id": cid,
        "missing": resp.get("missing") or [],
        "form": resp.get("form"),
        "hint": "Odpowiedz w polu lub wypełnij formularz i wyślij.",
    }
    _append_turn(session_id, message, out, clarify=True)
    return out


async def _ready_turn(
    *,
    session_id: str,
    message: str,
    cid: str | None,
    status: str,
    assistant: str,
    resp: dict[str, Any],
    scope_files: list[str] | None,
    scope_uris: list[str] | None,
    wait_for_confirmation: bool,
) -> dict[str, Any]:
    dsl = resp.get("dsl")
    action = nlp.primary_action(dsl)
    cfg = nlp.step_config(dsl)
    out = _nlp_output_base(cid, status)
    out.update(
        await _ready_action_payload(
            action,
            session_id=session_id,
            message=message,
            cfg=cfg,
            assistant=assistant,
            dsl=dsl,
            cid=cid,
            scope_files=scope_files,
            scope_uris=scope_uris,
            wait_for_confirmation=wait_for_confirmation,
        )
    )
    _append_turn(session_id, message, out, correlation=True)
    return out


async def _ready_action_payload(
    action: str | None,
    *,
    session_id: str,
    message: str,
    cfg: dict[str, Any],
    assistant: str,
    dsl: dict[str, Any] | None,
    cid: str | None,
    scope_files: list[str] | None,
    scope_uris: list[str] | None,
    wait_for_confirmation: bool,
) -> dict[str, Any]:
    if action == "system_file_list":
        return await _system_file_list_payload(session_id, message, scope_files, scope_uris)
    if action == "mullm_shell_task":
        return await _shell_task_payload(
            session_id,
            message,
            cfg,
            cid,
            wait_for_confirmation,
        )
    if action == "mullm_create_ticket":
        return await _ticket_payload(session_id, message, cfg, wait_for_confirmation)
    return {
        "reply": (
            assistant
            + "\n\n(Workflow gotowy — akcja poza Mullm; uruchom w nlp2dsl lub doprecyzuj.)"
        ),
        "dsl": dsl,
    }


async def _system_file_list_payload(
    session_id: str,
    message: str,
    scope_files: list[str] | None,
    scope_uris: list[str] | None,
) -> dict[str, Any]:
    scope_kind = chat_service.file_list_scope(message)
    inv = chat_service.filter_file_inventory(
        await chat_service.fetch_file_inventory(),
        scope_kind,
        scope_files=scope_files,
        scope_uris=scope_uris,
    )
    reply = chat_service.format_file_list_reply(
        inv,
        scope_files=scope_files,
        scope_uris=scope_uris,
        list_scope=scope_kind,
    )
    return {
        "reply": reply,
        "artifact": chat_service.build_file_list_artifact(
            reply,
            inv,
            session_id=session_id,
            list_scope=scope_kind,
        ),
        "executed": "mullm_file_list",
        "intent": "file_list",
        "inventory": inv,
    }


async def _shell_task_payload(
    session_id: str,
    message: str,
    cfg: dict[str, Any],
    cid: str | None,
    wait_for_confirmation: bool,
) -> dict[str, Any]:
    shell = cfg.get("shell_command") or _extract_shell(message)
    if not shell:
        return _shell_clarify_payload(cid)

    from app import workspace as ws

    title = cfg.get("title") or message[:80]
    policy = routing_policy.load_policy()
    session = get_or_create(session_id)
    agent = policy.agent_for_route(
        "mullm_shell",
        session_agent_id=session.context.agent_id or None,
    )
    result = await ws.create_task_immediate(
        session_id,
        title=title,
        description=message,
        shell_command=shell,
        wait_for_confirmation=wait_for_confirmation,
        agent_id=agent,
    )
    return {
        "task": result,
        "assigned_agent": agent,
        "reply": _task_reply(
            result,
            wait_for_confirmation=wait_for_confirmation,
            started=f"Uruchomiono ticket `{result.get('task_id')}` · `{shell}`",
        ),
        "executed": "mullm_shell",
    }


def _shell_clarify_payload(cid: str | None) -> dict[str, Any]:
    return {
        "reply": "Podaj polecenie shell (np. `run ls -la`).",
        "clarify": {
            "conversation_id": cid,
            "form": {
                "action": "mullm_shell_task",
                "fields": [
                    {
                        "name": "shell_command",
                        "type": "string",
                        "label": "Polecenie shell",
                        "required": True,
                    }
                ],
            },
            "missing": ["shell_command"],
        },
    }


async def _ticket_payload(
    session_id: str,
    message: str,
    cfg: dict[str, Any],
    wait_for_confirmation: bool,
) -> dict[str, Any]:
    from app import workspace as ws

    policy = routing_policy.load_policy()
    session = get_or_create(session_id)
    agent = policy.agent_for_route(
        "nlp2dsl",
        session_agent_id=session.context.agent_id or None,
    )
    result = await ws.create_task_immediate(
        session_id,
        title=cfg.get("title") or message[:80],
        description=cfg.get("description") or message,
        shell_command=None,
        wait_for_confirmation=wait_for_confirmation,
        agent_id=agent,
    )
    return {
        "task": result,
        "assigned_agent": agent,
        "reply": _task_reply(
            result,
            wait_for_confirmation=wait_for_confirmation,
            started=f"Utworzono i uruchomiono ticket `{result.get('task_id')}`.",
        ),
        "executed": "mullm_ticket",
    }


def _task_reply(
    result: dict[str, Any],
    *,
    wait_for_confirmation: bool,
    started: str,
) -> str:
    if not result.get("ok"):
        return f"Nie udało się: {result.get('error')}"
    tid = result.get("task_id")
    if wait_for_confirmation:
        return f"Ticket `{tid}` w kolejce — potwierdź na liście (◎)."
    return started


def _closed_turn(
    session_id: str,
    message: str,
    cid: str | None,
    status: str,
    assistant: str,
) -> dict[str, Any]:
    out = _nlp_output_base(cid, status)
    out["reply"] = assistant or "Rozmowa zakończona."
    _append_turn(session_id, message, out)
    return out


def _append_turn(
    session_id: str,
    message: str,
    out: dict[str, Any],
    *,
    clarify: bool = False,
    correlation: bool = False,
) -> None:
    chat_service._append(session_id, "user", message)
    if clarify:
        chat_service._append(session_id, "assistant", out["reply"], clarify=True)
    else:
        chat_service._append(session_id, "assistant", out["reply"])
    out["history"] = chat_service.get_history(session_id)
    if correlation:
        out["correlation_id"] = session_id


async def _mullm_file_list_turn(
    *,
    session_id: str,
    message: str,
    scope_files: list[str] | None,
    scope_uris: list[str] | None,
) -> dict[str, Any]:
    scope_kind = chat_service.file_list_scope(message)
    inv = chat_service.filter_file_inventory(
        await chat_service.fetch_file_inventory(),
        scope_kind,
        scope_files=scope_files,
        scope_uris=scope_uris,
    )
    reply = chat_service.format_file_list_reply(
        inv,
        scope_files=scope_files,
        scope_uris=scope_uris,
        list_scope=scope_kind,
    )
    chat_service._append(session_id, "user", message)
    chat_service._append(session_id, "assistant", reply)
    return {
        "reply": reply,
        "executed": "mullm_file_list",
        "intent": "file_list",
        "inventory": inv,
        "artifact": chat_service.build_file_list_artifact(
            reply,
            inv,
            session_id=session_id,
            list_scope=scope_kind,
        ),
        "history": chat_service.get_history(session_id),
        "correlation_id": session_id,
        "nlp2dsl_conversation_id": None,
    }


async def _fallback_turn(
    *,
    session_id: str,
    message: str,
    scope_files: list[str] | None,
    scope_uris: list[str] | None,
    prefix_note: str = "",
) -> dict[str, Any]:
    hint = _local_clarify(message)
    if hint:
        chat_service._append(session_id, "user", message)
        reply = prefix_note + hint["reply"]
        chat_service._append(session_id, "assistant", reply)
        return {
            "reply": reply,
            "clarify": hint.get("clarify"),
            "history": chat_service.get_history(session_id),
            "correlation_id": session_id,
            "nlp2dsl_conversation_id": None,
        }

    base = await chat_service.handle_message(
        session_id=session_id,
        message=message,
        use_rag=True,
        scope_files=scope_files,
        scope_uris=scope_uris,
    )
    if prefix_note and base.get("reply"):
        base["reply"] = prefix_note + base["reply"]
    base["nlp2dsl_conversation_id"] = None
    return base


def _local_clarify(message: str) -> dict[str, Any] | None:
    lowered = message.lower()
    if re.search(r"(utwórz|uruchom|wykonaj).*(zadanie|ticket|shell)", lowered):
        if not _extract_shell(message):
            return {
                "reply": "Chcesz uruchomić zadanie agenta — podaj polecenie shell (np. `ls -la`).",
                "clarify": {
                    "form": {
                        "fields": [
                            {
                                "name": "shell_command",
                                "type": "string",
                                "label": "Polecenie shell",
                                "required": True,
                            }
                        ]
                    },
                    "missing": ["shell_command"],
                },
            }
    return None


def _extract_shell(text: str) -> str | None:
    for prefix in ("run ", "exec ", "shell ", "wykonaj ", "uruchom "):
        if text.lower().strip().startswith(prefix):
            return text[len(prefix) :].strip()
    return None
