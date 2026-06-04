from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app import chat as chat_service
from app import nlp2dsl_bridge as nlp
from app import prompt_router
from app import routing_policy
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
    routing["nlp2dsl_invoked"] = bool(out.get("nlp2dsl_routing"))
    if out.get("nlp2dsl_routing"):
        routing["nlp2dsl"] = out["nlp2dsl_routing"]
    elif decision.route in ("mullm_file_list", "mullm_shell"):
        routing["nlp2dsl_skipped"] = True
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
    if not shell:
        return _missing_shell_response(session_id, decision)
    result = await _create_shell_task(
        session_id,
        message=message,
        shell=shell,
        wait_for_confirmation=wait_for_confirmation,
        agent=decision.policy_flags.get("assigned_agent"),
    )
    return _shell_route_response(session_id, message, decision, result)


def _missing_shell_response(
    session_id: str,
    decision: prompt_router.RouteDecision,
) -> dict[str, Any]:
    decision.requires_clarification = True
    prompt_router.record_route_event(
        session_id, decision, event_type="RouteFailed", outcome="no_shell"
    )
    out = {
        "reply": "Podaj polecenie shell (np. `run ls -la`).",
        "history": chat_service.get_history(session_id),
    }
    return _attach_routing(session_id, out, decision)


async def _create_shell_task(
    session_id: str,
    *,
    message: str,
    shell: str,
    wait_for_confirmation: bool,
    agent: str | None,
) -> dict[str, Any]:
    from app import workspace as ws

    return await ws.create_task_immediate(
        session_id,
        title=message[:80],
        description=message,
        shell_command=shell,
        wait_for_confirmation=wait_for_confirmation,
        agent_id=agent,
    )


def _shell_route_response(
    session_id: str,
    message: str,
    decision: prompt_router.RouteDecision,
    result: dict[str, Any],
) -> dict[str, Any]:
    agent = decision.policy_flags.get("assigned_agent")
    reply = _shell_task_reply(result, agent)
    chat_service._append(session_id, "user", message)
    chat_service._append(session_id, "assistant", reply)
    out = {
        "reply": reply,
        "task": result,
        "executed": "mullm_shell",
        "assigned_agent": agent,
        "history": chat_service.get_history(session_id),
    }
    prompt_router.record_route_event(session_id, decision, outcome="succeeded")
    return _attach_routing(session_id, out, decision)


def _shell_task_reply(result: dict[str, Any], agent: str | None) -> str:
    return (
        f"Ticket `{result.get('task_id', '?')}`"
        + (f" → agent `{agent}`" if agent and result.get("ok") else "")
        + (" w kolejce." if result.get("ok") else f" — {result.get('error')}")
    )


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
    Pipeline ingress z routing_policy.yaml (domyślnie: rag_probe → rules → nlp2dsl → rag_answer).
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
        return pipeline_result
    return await _fallback_routed_turn(state)


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


async def _run_ingress_pipeline(state: TurnState) -> dict[str, Any] | None:
    handlers = {
        "rag_probe": _rag_probe_step,
        "rules": _rules_step,
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
    if not (state.use_rag and state.policy.rag_probe.enabled):
        return None
    if _should_skip_rag_probe(state):
        return None

    probe = await chat_service.probe_rag(
        session_id=state.session_id,
        message=state.message,
        limit=state.policy.rag_probe.search_limit,
    )
    hits = int(probe.get("hits") or 0)
    state.pipeline_ctx["rag_probe_hits"] = hits
    if hits < state.policy.rag_probe.min_hits or not state.policy.rag_probe.answer_on_hit:
        return None

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
    return bool(settings.skip_shell_prefix and prompt_router._shell_prefix(state.message))


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
    """Reguły ingress już obsłużyły trasę — nie wołaj nlp2dsl ponownie."""
    if state.decision and state.decision.route in ("mullm_file_list", "mullm_shell"):
        return True
    if chat_service.is_file_list_intent(state.message):
        return True
    return bool(prompt_router._shell_prefix(state.message))


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

    if status == "in_progress":
        out = _in_progress_turn(session_id, message, resp, cid, status, assistant)
    elif status == "ready":
        out = await _ready_turn(
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
    else:
        out = _closed_turn(session_id, message, cid, status, assistant)

    if nlp_routing:
        out["nlp2dsl_routing"] = nlp_routing
    return out


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
