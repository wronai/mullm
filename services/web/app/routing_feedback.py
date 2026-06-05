"""
Ocena tras routingu przez użytkownika → tickety poprawy → propozycje ewolucji polityki.

Zapis: JSONL w data/routing_feedback/ (powiązanie z decision_tree, logami sesji).
Nie mutuje automatycznie routing_policy.yaml — generuje learnings do przeglądu.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from app import chat as chat_service
from app.workspace import get_or_create

Rating = Literal["good", "partial", "bad"]

_VALID_RATINGS = frozenset({"good", "partial", "bad"})


@dataclass
class RoutingFeedbackRecord:
    feedback_id: str
    session_id: str
    turn_id: str
    rating: Rating
    user_message: str
    actual_route: str | None = None
    expected_route: str | None = None
    expected_reply_hint: str = ""
    improvement_notes: str = ""
    tags: list[str] = field(default_factory=list)
    routing: dict[str, Any] = field(default_factory=dict)
    decision_tree: dict[str, Any] = field(default_factory=dict)
    improvement_ticket_id: str | None = None
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "feedback_id": self.feedback_id,
            "session_id": self.session_id,
            "turn_id": self.turn_id,
            "rating": self.rating,
            "user_message": self.user_message,
            "actual_route": self.actual_route,
            "expected_route": self.expected_route,
            "expected_reply_hint": self.expected_reply_hint,
            "improvement_notes": self.improvement_notes,
            "tags": self.tags,
            "routing": self.routing,
            "decision_tree": self.decision_tree,
            "improvement_ticket_id": self.improvement_ticket_id,
            "created_at": self.created_at,
        }


def feedback_dir() -> Path:
    env = os.getenv("MULLM_FEEDBACK_DIR", "").strip()
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent / "data" / "routing_feedback"


def _feedback_path() -> Path:
    d = feedback_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d / "feedback.jsonl"


def _improvements_path() -> Path:
    d = feedback_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d / "improvements.jsonl"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _find_turn_context(
    session_id: str,
    turn_id: str,
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Ostatnia wiadomość usera przed asystentem z danym turn_id."""
    history = chat_service.get_history(session_id)
    user_msg = ""
    routing: dict[str, Any] = {}
    tree: dict[str, Any] = {}
    for i, item in enumerate(history):
        if item.get("role") != "assistant":
            continue
        tr = item.get("routing") or {}
        if tr.get("turn_id") != turn_id:
            continue
        routing = tr
        tree = tr.get("decision_tree") or {}
        for j in range(i - 1, -1, -1):
            if history[j].get("role") == "user":
                user_msg = history[j].get("content") or ""
                break
        break
    return user_msg, routing, tree


def _resolve_feedback_inputs(
    session_id: str,
    turn_id: str,
    user_message: str | None,
    routing: dict[str, Any] | None,
    decision_tree: dict[str, Any] | None,
) -> tuple[str, dict[str, Any], dict[str, Any], str | None]:
    msg, hist_routing, hist_tree = _find_turn_context(session_id, turn_id)
    user_message = (user_message or msg).strip()
    resolved_routing = routing or hist_routing
    resolved_tree = decision_tree or hist_tree or resolved_routing.get("decision_tree") or {}
    actual_route = resolved_routing.get("route")
    return user_message, resolved_routing, resolved_tree, actual_route


def _build_feedback_tags(
    rating: str,
    actual_route: str | None,
    expected_route: str | None,
    improvement_notes: str,
    tags: list[str] | None,
) -> list[str]:
    tag_list = list(tags or [])
    if rating == "bad" and expected_route and actual_route and expected_route != actual_route:
        tag_list.append("route_mismatch")
    if rating == "bad" and improvement_notes:
        tag_list.append("needs_policy_change")
    return tag_list


def record_feedback(
    *,
    session_id: str,
    turn_id: str,
    rating: str,
    expected_route: str | None = None,
    expected_reply_hint: str = "",
    improvement_notes: str = "",
    tags: list[str] | None = None,
    user_message: str | None = None,
    routing: dict[str, Any] | None = None,
    decision_tree: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if rating not in _VALID_RATINGS:
        raise ValueError(f"rating must be one of {sorted(_VALID_RATINGS)}")

    user_message, routing, decision_tree, actual_route = _resolve_feedback_inputs(
        session_id, turn_id, user_message, routing, decision_tree
    )
    tag_list = _build_feedback_tags(rating, actual_route, expected_route, improvement_notes, tags)

    improvement_ticket: dict[str, Any] | None = None
    ticket_id: str | None = None
    if rating in ("bad", "partial"):
        improvement_ticket = _create_improvement_ticket(
            session_id=session_id,
            turn_id=turn_id,
            user_message=user_message,
            actual_route=actual_route,
            expected_route=expected_route,
            expected_reply_hint=expected_reply_hint,
            improvement_notes=improvement_notes,
            rating=rating,
            tags=tag_list,
            routing=routing,
            decision_tree=decision_tree,
        )
        ticket_id = improvement_ticket["ticket_id"]

    record = RoutingFeedbackRecord(
        feedback_id=str(uuid.uuid4()),
        session_id=session_id,
        turn_id=turn_id,
        rating=rating,  # type: ignore[arg-type]
        user_message=user_message,
        actual_route=actual_route,
        expected_route=expected_route,
        expected_reply_hint=(expected_reply_hint or "").strip(),
        improvement_notes=(improvement_notes or "").strip(),
        tags=tag_list,
        routing=routing,
        decision_tree=decision_tree,
        improvement_ticket_id=ticket_id,
        created_at=_now_iso(),
    )
    _append_jsonl(_feedback_path(), record.to_dict())

    session = get_or_create(session_id)
    session.add_event(
        "RouteFeedbackRecorded",
        f"{rating}: {actual_route or '?'}",
        feedback_id=record.feedback_id,
        turn_id=turn_id,
        rating=rating,
        improvement_ticket_id=ticket_id,
    )

    out = record.to_dict()
    if improvement_ticket:
        out["improvement_ticket"] = improvement_ticket
    return out


def _create_improvement_ticket(
    *,
    session_id: str,
    turn_id: str,
    user_message: str,
    actual_route: str | None,
    expected_route: str | None,
    expected_reply_hint: str,
    improvement_notes: str,
    rating: str,
    tags: list[str],
    routing: dict[str, Any],
    decision_tree: dict[str, Any],
) -> dict[str, Any]:
    ticket_id = str(uuid.uuid4())
    suggestions = _suggest_actions(
        user_message=user_message,
        actual_route=actual_route,
        expected_route=expected_route,
        improvement_notes=improvement_notes,
        decision_tree=decision_tree,
    )
    ticket = {
        "schema": "mullm.routing.improvement_ticket.v1",
        "ticket_id": ticket_id,
        "status": "open",
        "session_id": session_id,
        "turn_id": turn_id,
        "rating": rating,
        "user_message": user_message,
        "actual_route": actual_route,
        "expected_route": expected_route,
        "expected_reply_hint": expected_reply_hint,
        "improvement_notes": improvement_notes,
        "tags": tags,
        "suggested_actions": suggestions,
        "decision_tree": decision_tree,
        "routing_snapshot": routing,
        "created_at": _now_iso(),
    }
    _append_jsonl(_improvements_path(), ticket)
    get_or_create(session_id).add_event(
        "RoutingImprovementTicket",
        f"open: {actual_route} → {expected_route or '?'}",
        ticket_id=ticket_id,
        suggested_actions=suggestions,
    )
    _maybe_sync_planfile(ticket, session_id=session_id)
    return ticket


def _maybe_sync_planfile(ticket: dict[str, Any], *, session_id: str) -> None:
    from app.planfile_bridge import sync_improvement_ticket

    result = sync_improvement_ticket(ticket)
    if not result:
        return
    if result.get("ok") and result.get("planfile_id"):
        ticket["planfile_id"] = result["planfile_id"]
        get_or_create(session_id).add_event(
            "PlanfileTicketSynced",
            f"planfile:{result['planfile_id']}",
            planfile_id=result["planfile_id"],
            mullm_ticket_id=ticket.get("ticket_id"),
        )
    elif not result.get("ok"):
        get_or_create(session_id).add_event(
            "PlanfileTicketSyncFailed",
            (result.get("detail") or "planfile sync failed")[:120],
        )


def _suggest_actions(
    *,
    user_message: str,
    actual_route: str | None,
    expected_route: str | None,
    improvement_notes: str,
    decision_tree: dict[str, Any],
) -> list[str]:
    actions: list[str] = []
    if expected_route and actual_route and expected_route != actual_route:
        actions.append(
            f"Dopisz/zweryfikuj regułę dla trasy `{expected_route}` "
            f"(obecnie: `{actual_route}`)."
        )
        actions.append(
            f"Rozważ wpis w user_expectations (routing_policy.yaml) "
            f"dla frazy: „{user_message[:80]}”."
        )
    selected = decision_tree.get("selected_step")
    if selected:
        actions.append(
            f"Sprawdź krok ingress `{selected}` w drzewie — czy checks/rule_nodes są kompletne."
        )
    if improvement_notes:
        actions.append(f"Notatka użytkownika: {improvement_notes[:200]}")
    if not actions:
        actions.append("Przejrzyj decision_tree i logi sesji; doprecyzuj expected_route przy kolejnej ocenie.")
    return actions


def list_feedback(
    *,
    session_id: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    rows = _read_jsonl_tail(_feedback_path(), limit=limit * 3)
    if session_id:
        rows = [r for r in rows if r.get("session_id") == session_id]
    return rows[-limit:]


def list_improvement_tickets(*, status: str = "open", limit: int = 30) -> list[dict[str, Any]]:
    rows = _read_jsonl_tail(_improvements_path(), limit=500)
    if status:
        rows = [r for r in rows if r.get("status") == status]
    return rows[-limit:]


def aggregate_learnings(*, limit: int = 20) -> dict[str, Any]:
    """Propozycje ewolucji polityki z zebranych ocen (do przeglądu operatora)."""
    feedback = _read_jsonl_tail(_feedback_path(), limit=2000)
    bad = [f for f in feedback if f.get("rating") in ("bad", "partial")]
    mismatches: dict[str, int] = {}
    phrase_routes: dict[str, dict[str, int]] = {}

    for f in bad:
        exp = f.get("expected_route")
        act = f.get("actual_route")
        if exp and act and exp != act:
            key = f"{act}→{exp}"
            mismatches[key] = mismatches.get(key, 0) + 1
        msg = (f.get("user_message") or "").strip().lower()[:120]
        if msg and exp:
            phrase_routes.setdefault(msg, {})
            phrase_routes[msg][exp] = phrase_routes[msg].get(exp, 0) + 1

    proposals: list[dict[str, Any]] = []
    for msg, routes in sorted(phrase_routes.items(), key=lambda x: -sum(x[1].values()))[:limit]:
        best_route = max(routes.items(), key=lambda x: x[1])[0]
        proposals.append(
            {
                "type": "user_expectation",
                "match_phrases": [msg],
                "suggested_route": best_route,
                "evidence_count": sum(routes.values()),
                "yaml_hint": {
                    "id": f"learned_{uuid.uuid4().hex[:8]}",
                    "match": {"phrases": [msg]},
                    "route": best_route,
                    "reason_codes": ["learned_from_feedback"],
                    "standard": f"Ustalone z {sum(routes.values())} ocen użytkownika",
                },
            }
        )

    open_tickets = list_improvement_tickets(status="open", limit=50)
    return {
        "schema": "mullm.routing.learnings.v1",
        "generated_at": _now_iso(),
        "stats": {
            "feedback_total": len(feedback),
            "negative_total": len(bad),
            "route_mismatches": mismatches,
            "open_improvement_tickets": len(open_tickets),
        },
        "proposals": proposals,
        "open_improvement_tickets": open_tickets[:10],
        "principles": [
            "Oceny zapisują decision_tree + routing — można odtworzyć decyzję bez zgadywania.",
            "Tickety poprawy (improvement_ticket) są otwarte do ręcznego wdrożenia w YAML/kodzie.",
            "proposals to sugestie user_expectations — nie stosuj automatycznie bez review.",
        ],
    }


def _append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _read_jsonl_tail(path: Path, *, limit: int) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[dict[str, Any]] = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def new_turn_id() -> str:
    return str(uuid.uuid4())
