"""
Drzewo decyzji routingu — transparentny podgląd ingress i reguł.

Używane przez:
- conductor (trace na żywo podczas tury),
- GET /api/routing/explain (symulacja bez wykonania handlerów),
- workspace UI (panel drzewa decyzji).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app import chat as chat_service
from app import prompt_router
from app import routing_policy

StepStatus = Literal["skipped", "passed", "selected", "would_select", "no_match"]


@dataclass
class TraceCheck:
    id: str
    label: str
    passed: bool
    detail: str = ""
    intract_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "passed": self.passed,
            "detail": self.detail,
            "intract_id": self.intract_id,
        }


@dataclass
class TraceStep:
    step: str
    status: StepStatus
    summary: str
    checks: list[TraceCheck] = field(default_factory=list)
    decision: dict[str, Any] | None = None
    rule_nodes: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "status": self.status,
            "summary": self.summary,
            "checks": [c.to_dict() for c in self.checks],
            "decision": self.decision,
            "rule_nodes": self.rule_nodes,
        }


@dataclass
class DecisionTree:
    message: str
    chat_mode: str
    use_rag: bool
    ingress_order: list[str]
    steps: list[TraceStep] = field(default_factory=list)
    selected_step: str | None = None
    final_route: str | None = None
    matched_expectations: list[dict[str, Any]] = field(default_factory=list)
    principles: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "mullm.routing.decision_tree.v1",
            "message": self.message,
            "chat_mode": self.chat_mode,
            "use_rag": self.use_rag,
            "ingress_order": self.ingress_order,
            "steps": [s.to_dict() for s in self.steps],
            "selected_step": self.selected_step,
            "final_route": self.final_route,
            "matched_expectations": self.matched_expectations,
            "principles": self.principles,
        }


def new_trace(
    *,
    message: str,
    chat_mode: str,
    use_rag: bool,
    policy: routing_policy.RoutingPolicy | None = None,
) -> DecisionTree:
    pol = policy or routing_policy.load_policy()
    return DecisionTree(
        message=(message or "").strip(),
        chat_mode=chat_mode,
        use_rag=use_rag,
        ingress_order=pol.ingress_for_mode(chat_mode),
        principles=_default_principles(),
    )


def append_step(trace: DecisionTree, step: TraceStep) -> None:
    trace.steps.append(step)
    if step.status == "selected":
        trace.selected_step = step.step
        if step.decision:
            trace.final_route = step.decision.get("route")


def _is_expectation_hit(text: str, spec: dict[str, Any]) -> tuple[bool, int]:
    match_block = spec.get("match") or {}
    phrases = [str(p).lower() for p in match_block.get("phrases") or []]
    if not phrases:
        return False, 0
    excludes = [str(p).lower() for p in match_block.get("exclude_phrases") or []]
    if any(ex in text for ex in excludes):
        return False, 0
    hit_phrases = [p for p in phrases if p in text]
    if not hit_phrases:
        return False, 0
    return True, max(len(p) for p in hit_phrases)


def match_user_expectations(
    message: str,
    policy: routing_policy.RoutingPolicy,
) -> list[dict[str, Any]]:
    text = (message or "").strip().lower()
    if not text:
        return []
    matched: list[dict[str, Any]] = []
    for spec in policy.user_expectations:
        hit, match_len = _is_expectation_hit(text, spec)
        if not hit:
            continue
        matched.append(
            {
                "id": spec.get("id"),
                "route": spec.get("route"),
                "reason_codes": list(spec.get("reason_codes") or []),
                "standard": spec.get("standard", ""),
                "_match_len": match_len,
            }
        )
    matched.sort(key=lambda item: int(item.get("_match_len") or 0), reverse=True)
    for item in matched:
        item.pop("_match_len", None)
    return matched


def _node_empty(passed: bool) -> dict[str, Any]:
    return {
        "id": "rules.empty",
        "label": "Wiadomość niepusta",
        "passed": passed,
        "intract_id": "",
    }


def _node_mode_override(chat_mode: str, passed: bool) -> dict[str, Any]:
    return {
        "id": "rules.mode_override",
        "label": f"Nadpisanie trybu ({chat_mode})",
        "passed": passed,
        "detail": "search_context→rag, run_task→shell" if passed else "discuss — dalej",
        "intract_id": "",
    }


def _node_continue() -> dict[str, Any]:
    return {
        "id": "rules.continue",
        "label": "Kontynuuj / continue",
        "passed": True,
        "detail": "workroom_hint lub nlp2dsl resume",
        "intract_id": "",
    }


def _node_file_list(text: str, file_list: bool) -> dict[str, Any]:
    scope = chat_service.file_list_scope(text) if file_list else None
    return {
        "id": "rules.file_list",
        "label": "Lista plików z rejestru (nie shell)",
        "passed": file_list,
        "detail": f"scope={scope}" if file_list else "brak dopasowania intencji file_list",
        "intract_id": "mullm.route.file_list.decide",
        "checks": _file_list_checks(text) if file_list else [],
        "selected_route": "mullm_file_list" if file_list else None,
    }


def _node_shell_prefix(shell_prefix: bool) -> dict[str, Any]:
    return {
        "id": "rules.shell_prefix",
        "label": "Jawny prefix run/exec/shell",
        "passed": shell_prefix,
        "detail": "mullm_shell" if shell_prefix else "brak",
        "intract_id": "mullm.route.shell_prefix.decide",
        "selected_route": "mullm_shell" if shell_prefix else None,
    }


def _node_shell_nl(shell_nl: bool) -> dict[str, Any]:
    return {
        "id": "rules.shell_nl",
        "label": "NL → shell (nlp2cmd, krok agent_shell)",
        "passed": shell_nl,
        "detail": "nlp2cmd_shell w agent_shell" if shell_nl else "nie w rules — może agent_shell",
        "intract_id": "mullm.intent.shell_nl.detect",
    }


def _node_default_discuss() -> dict[str, Any]:
    return {
        "id": "rules.default_discuss",
        "label": "Domyślny discuss",
        "passed": True,
        "detail": "nlp2dsl (fallback rag)",
        "intract_id": "",
        "selected_route": "nlp2dsl",
    }


def build_rules_rule_nodes(message: str, *, chat_mode: str, use_rag: bool) -> list[dict[str, Any]]:
    """Kaskada reguł prompt_router (bez LLM) — węzły do drzewa."""
    text = (message or "").strip()
    nodes: list[dict[str, Any]] = []

    nodes.append(_node_empty(bool(text)))
    if not text:
        return nodes

    mode_hit = chat_mode in ("search_context", "run_task")
    nodes.append(_node_mode_override(chat_mode, mode_hit))
    if mode_hit:
        return nodes

    if chat_service.is_continue_intent(text):
        nodes.append(_node_continue())
        return nodes

    file_list = chat_service.is_file_list_intent(text)
    nodes.append(_node_file_list(text, file_list))
    if file_list:
        return nodes

    shell_prefix = prompt_router._shell_prefix(text)
    nodes.append(_node_shell_prefix(shell_prefix))
    if shell_prefix:
        return nodes

    shell_nl = chat_service.is_shell_nl_intent(text)
    nodes.append(_node_shell_nl(shell_nl))

    nodes.append(_node_default_discuss())
    return nodes


def _file_list_checks(text: str) -> list[dict[str, Any]]:
    from app.chat import _FILE_LIST_INTENT

    checks: list[dict[str, Any]] = []
    regex_hit = bool(_FILE_LIST_INTENT.search(text))
    checks.append(
        {
            "id": "detect.regex_file_list",
            "label": "Regex file_list",
            "passed": regex_hit,
            "intract_id": "mullm.intent.file_list.detect",
        }
    )
    checks.append(
        {
            "id": "detect.scope_user",
            "label": "Zakres user (usera/użytkownika)",
            "passed": chat_service.file_list_scope(text) == "user",
            "detail": f"scope={chat_service.file_list_scope(text)}",
        }
    )
    checks.append(
        {
            "id": "forbid.shell_prefix",
            "label": "Bez jawnego shell prefix",
            "passed": not prompt_router._shell_prefix(text),
            "intract_id": "mullm.route.file_list.decide",
        }
    )
    checks.append(
        {
            "id": "forbid.shell_nl",
            "label": "Nie traktuj jako shell_nl",
            "passed": not chat_service.is_shell_nl_intent(text) or chat_service.is_file_list_intent(text),
        }
    )
    return checks


def _default_principles() -> list[str]:
    return [
        "Ingress: routing_policy.yaml — nlp2dsl_resume → nlp2dsl_orient → rag_probe → rules (rescue) → agent_shell → nlp2dsl → rag_answer.",
        "nlp2dsl_orient jest pierwszym źródłem semantyki; rules/nlp2cmd tylko gdy orient=unknown.",
        "lista plikow usera (bez rejestru) → orient file_list_host → ls /host-home; github → /host-home/github; z rejestru → mullm_file_list.",
        "nlp2cmd tłumaczy shell-NL tylko gdy orient wskazał shell bez gotowego shell_command.",
        "Oczekiwania (user_expectations) dokumentują standardy — nie zastępują orientacji w runtime.",
    ]


async def explain_pipeline(
    message: str,
    *,
    chat_mode: str = "discuss",
    use_rag: bool = True,
    session_id: str | None = None,
) -> dict[str, Any]:
    """
    Symulacja drzewa decyzji (bez wykonania handlerów file_list/shell/nlp2dsl).
    Opcjonalnie probe RAG gdy session_id podany.
    """
    policy = routing_policy.load_policy()
    trace = new_trace(message=message, chat_mode=chat_mode, use_rag=use_rag, policy=policy)
    trace.matched_expectations = match_user_expectations(message, policy)
    text = trace.message

    rules_decision: prompt_router.RouteDecision | None = None
    selected: str | None = None

    for step_name in trace.ingress_order:
        if selected:
            append_step(
                trace,
                TraceStep(
                    step=step_name,
                    status="skipped",
                    summary=f"Pominięty — wybrano krok `{selected}`",
                ),
            )
            continue

        if step_name == "nlp2dsl_resume":
            step = TraceStep(
                step="nlp2dsl_resume",
                status="candidate",
                summary="Wznowienie nlp2dsl — dopytania gdy conversation_id + in_progress",
            )
        elif step_name == "nlp2dsl_orient":
            from app.routing.decision import OrientationDecision
            from app.routing.execution_resolver import route_from_orientation
            from app.local_orient import orient_query

            o = orient_query(text, connector="mullm")
            orient_model = OrientationDecision.from_dict(o.to_dict())
            orient_decision = route_from_orientation(orient_model) if orient_model else None
            actionable = o.category not in ("unknown", "system_local")
            summary = f"Orientacja ({o.source}): {o.category}"
            if o.shell_command:
                summary += f" → `{o.shell_command[:80]}`"
            elif o.suggested_action:
                summary += f" → {o.suggested_action}"
            step = TraceStep(
                step="nlp2dsl_orient",
                status="selected" if actionable and orient_decision else "passed",
                summary=summary,
                decision=orient_decision.to_dict() if orient_decision else {"orientation": o.to_dict()},
            )
            if step.status == "selected" and orient_decision:
                trace.final_route = orient_decision.route
        elif step_name == "rag_probe":
            step = await _explain_rag_probe(
                text, use_rag=use_rag, policy=policy, session_id=session_id
            )
        elif step_name == "rules":
            step, rules_decision = await _explain_rules_step(
                text, chat_mode=chat_mode, use_rag=use_rag
            )
        elif step_name == "agent_shell":
            step = _explain_agent_shell(text, rules_decision=rules_decision)
        elif step_name == "nlp2dsl":
            step = _explain_nlp2dsl(text, rules_decision=rules_decision)
        elif step_name == "rag_answer":
            step = _explain_rag_answer(use_rag=use_rag)
        else:
            step = TraceStep(step=step_name, status="skipped", summary="Nieznany krok")

        append_step(trace, step)
        if step.status == "selected":
            selected = step_name

    if rules_decision and not trace.final_route:
        trace.final_route = rules_decision.route

    out = trace.to_dict()
    if rules_decision:
        out["router_decision"] = rules_decision.to_dict()
    return out


def _build_rag_probe_checks(
    use_rag: bool,
    rp: Any,
    skip_file: bool,
    skip_shell: bool,
    skip_nl: bool,
) -> list[TraceCheck]:
    return [
        TraceCheck("use_rag", "use_rag=true", use_rag),
        TraceCheck("rag.enabled", "rag_probe.enabled", rp.enabled),
        TraceCheck(
            "skip.file_list",
            "skip przy file_list (policy)",
            skip_file,
            detail="skip_file_list_intent" if skip_file else "",
        ),
        TraceCheck(
            "skip.shell_prefix",
            "skip przy run/exec",
            skip_shell,
        ),
        TraceCheck("skip.shell_nl", "skip przy shell_nl", skip_nl),
    ]


def _check_rag_probe_skipped(
    use_rag: bool,
    rp: Any,
    skip_file: bool,
    skip_shell: bool,
    skip_nl: bool,
    checks: list[TraceCheck],
) -> TraceStep | None:
    if not use_rag or not rp.enabled:
        return TraceStep(
            step="rag_probe",
            status="skipped",
            summary="RAG wyłączony lub rag_probe.enabled=false",
            checks=checks,
        )
    if skip_file or skip_shell or skip_nl:
        reason = "skip_file_list_intent" if skip_file else ("skip_shell_prefix" if skip_shell else "shell_nl")
        return TraceStep(
            step="rag_probe",
            status="skipped",
            summary=f"Pominięty ({reason})",
            checks=checks,
        )
    return None


def _evaluate_rag_probe_hits(
    rp: Any,
    hits: int,
    checks: list[TraceCheck],
) -> TraceStep:
    if rp.answer_on_hit and hits >= rp.min_hits:
        dec = prompt_router.RouteDecision(
            route="rag",
            handler="chat.handle_message.rag",
            intent="rag_probe_answer",
            confidence=0.85,
            reason="answer_on_hit",
            reason_codes=["rag_probe", "answer_on_hit"],
        )
        return TraceStep(
            step="rag_probe",
            status="selected",
            summary=f"RAG odpowiedź ({hits} trafień)",
            checks=checks,
            decision=dec.to_dict(),
        )
    return TraceStep(
        step="rag_probe",
        status="passed",
        summary="Probe OK, bez answer_on_hit — dalej pipeline",
        checks=checks,
    )


async def _explain_rag_probe(
    text: str,
    *,
    use_rag: bool,
    policy: routing_policy.RoutingPolicy,
    session_id: str | None,
) -> TraceStep:
    rp = policy.rag_probe
    skip_file = rp.skip_file_list_intent and chat_service.is_file_list_intent(text)
    skip_shell = rp.skip_shell_prefix and prompt_router._shell_prefix(text)
    skip_nl = chat_service.is_shell_nl_intent(text)

    checks = _build_rag_probe_checks(use_rag, rp, skip_file, skip_shell, skip_nl)
    skipped_step = _check_rag_probe_skipped(use_rag, rp, skip_file, skip_shell, skip_nl, checks)
    if skipped_step:
        return skipped_step

    hits = 0
    if session_id:
        probe = await chat_service.probe_rag(
            session_id=session_id,
            message=text,
            limit=rp.search_limit,
        )
        hits = int(probe.get("hits") or 0)
        checks.append(
            TraceCheck(
                "rag.hits",
                f"trafienia RAG (limit={rp.search_limit})",
                hits >= rp.min_hits,
                detail=f"hits={hits}",
            )
        )

    return _evaluate_rag_probe_hits(rp, hits, checks)


async def _explain_rules_step(
    text: str,
    *,
    chat_mode: str,
    use_rag: bool,
) -> tuple[TraceStep, prompt_router.RouteDecision | None]:
    rule_nodes = build_rules_rule_nodes(text, chat_mode=chat_mode, use_rag=use_rag)

    if chat_service.is_continue_intent(text):
        dec = prompt_router.RouteDecision(
            route="workroom_hint",
            handler="conductor._continue_clarify_turn",
            intent="session_continue",
            confidence=0.88,
            reason="kontynuuj",
            reason_codes=["intent_continue", "clarify_next_step"],
        )
        return (
            TraceStep(
                step="rules",
                status="selected",
                summary="Kontynuuj → workroom_hint / nlp2dsl resume",
                rule_nodes=rule_nodes,
                decision=dec.to_dict(),
            ),
            dec,
        )

    decision = await prompt_router.decide_route(
        text,
        chat_mode=chat_mode,
        use_rag=use_rag,
        policy_flags={"pipeline_step": "rules"},
    )
    executable = decision.route in ("mullm_file_list", "mullm_shell", "nlp2cmd_shell")
    if executable:
        return (
            TraceStep(
                step="rules",
                status="selected",
                summary=f"Reguły → {decision.route} ({decision.reason})",
                rule_nodes=rule_nodes,
                decision=decision.to_dict(),
            ),
            decision,
        )
    return (
        TraceStep(
            step="rules",
            status="passed",
            summary=f"Reguły: {decision.route} — wykonanie w agent_shell/nlp2dsl",
            rule_nodes=rule_nodes,
            decision=decision.to_dict(),
        ),
        decision,
    )


def _explain_agent_shell(
    text: str,
    *,
    rules_decision: prompt_router.RouteDecision | None,
) -> TraceStep:
    if rules_decision and rules_decision.route in ("mullm_file_list", "mullm_shell", "nlp2cmd_shell"):
        return TraceStep(
            step="agent_shell",
            status="skipped",
            summary=f"rules już obsłużyły `{rules_decision.route}`",
        )
    nl = chat_service.is_shell_nl_intent(text)
    checks = [
        TraceCheck(
            "intent.shell_nl",
            "is_shell_nl_intent",
            nl,
            intract_id="mullm.intent.shell_nl.detect",
        ),
        TraceCheck(
            "not.file_list",
            "nie file_list",
            not chat_service.is_file_list_intent(text),
        ),
    ]
    if not nl:
        return TraceStep(
            step="agent_shell",
            status="skipped",
            summary="Brak intencji NL shell",
            checks=checks,
        )
    dec = prompt_router.RouteDecision(
        route="nlp2cmd_shell",
        handler="workspace.create_task_immediate",
        intent="shell_nlp2cmd",
        confidence=0.88,
        reason="agent_shell / nlp2cmd (symulacja)",
        reason_codes=["ingress_agent_shell", "nlp2cmd_translate"],
    )
    return TraceStep(
        step="agent_shell",
        status="would_select",
        summary="NL shell → nlp2cmd → ticket shell_agent (wymaga healthy nlp2cmd)",
        checks=checks,
        decision=dec.to_dict(),
    )


def _explain_nlp2dsl(
    text: str,
    *,
    rules_decision: prompt_router.RouteDecision | None,
) -> TraceStep:
    skip_reasons: list[str] = []
    if rules_decision and rules_decision.route in ("mullm_file_list", "mullm_shell", "nlp2cmd_shell"):
        skip_reasons.append(f"rules:{rules_decision.route}")
    if chat_service.is_file_list_intent(text):
        skip_reasons.append("file_list_guard")
    if prompt_router._shell_prefix(text):
        skip_reasons.append("shell_prefix_guard")
    if chat_service.is_shell_nl_intent(text):
        skip_reasons.append("shell_nl_via_agent_shell")

    if skip_reasons:
        return TraceStep(
            step="nlp2dsl",
            status="skipped",
            summary="Pominięty: " + ", ".join(skip_reasons),
            checks=[
                TraceCheck("guard", r, True, detail=r) for r in skip_reasons
            ],
        )

    route = rules_decision.route if rules_decision else "nlp2dsl"
    dec = rules_decision or prompt_router.decide_route_rules(text)
    return TraceStep(
        step="nlp2dsl",
        status="would_select",
        summary=f"Delegacja workflow → nlp2dsl ({route})",
        decision=dec.to_dict(),
    )


def _explain_rag_answer(*, use_rag: bool) -> TraceStep:
    if not use_rag:
        return TraceStep(step="rag_answer", status="skipped", summary="use_rag=false")
    dec = prompt_router.RouteDecision(
        route="rag",
        handler="chat.handle_message.rag",
        intent="rag_pipeline",
        confidence=0.5,
        reason="rag_answer",
        reason_codes=["ingress_rag_answer"],
    )
    return TraceStep(
        step="rag_answer",
        status="would_select",
        summary="Odpowiedź RAG (gdy wcześniejsze kroki bez wyniku)",
        decision=dec.to_dict(),
    )


def _orient_category_to_route(category: str) -> str:
    return {
        "file_list_registry": "mullm_file_list",
        "file_list_host": "nlp2cmd_shell",
        "shell": "nlp2cmd_shell",
        "workflow": "nlp2dsl",
    }.get(category, "unknown")


_INGRESS_STEP_FOR_ROUTE: dict[str, str] = {
    "mullm_file_list": "nlp2dsl_orient",
    "mullm_shell": "nlp2dsl_orient",
    "workroom_hint": "rules",
    "nlp2cmd_shell": "nlp2dsl_orient",
    "nlp2dsl": "nlp2dsl_orient",
    "rag": "rag_answer",
    "unknown": "nlp2dsl",
}


def align_tree_to_route(
    tree: dict[str, Any],
    actual_route: str,
    *,
    ingress_step: str | None = None,
) -> dict[str, Any]:
    """Dopasuj symulację do faktycznej trasy wykonanej w turze."""
    expected = ingress_step or _INGRESS_STEP_FOR_ROUTE.get(actual_route, "nlp2dsl")
    if actual_route == "rag" and any(
        s.get("step") == "rag_probe" and s.get("status") == "selected"
        for s in tree.get("steps") or []
    ):
        expected = "rag_probe"
    tree["selected_step"] = expected
    tree["final_route"] = actual_route
    seen = False
    for step in tree.get("steps") or []:
        name = step.get("step")
        if name == expected:
            step["status"] = "selected"
            step["summary"] = (step.get("summary") or "") + " [wykonano]"
            seen = True
        elif not seen:
            if step.get("status") == "would_select":
                step["status"] = "passed"
        else:
            step["status"] = "skipped"
    return tree


def record_live_step(
    trace: DecisionTree,
    *,
    step: str,
    status: StepStatus,
    summary: str,
    checks: list[TraceCheck] | None = None,
    decision: dict[str, Any] | None = None,
    rule_nodes: list[dict[str, Any]] | None = None,
) -> None:
    append_step(
        trace,
        TraceStep(
            step=step,
            status=status,
            summary=summary,
            checks=checks or [],
            decision=decision,
            rule_nodes=rule_nodes or [],
        ),
    )
