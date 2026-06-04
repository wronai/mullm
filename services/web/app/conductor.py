from __future__ import annotations

import re
from typing import Any

from app import chat as chat_service
from app import nlp2dsl_bridge as nlp


async def handle_turn(
    *,
    session_id: str,
    message: str,
    nlp_conversation_id: str | None,
    scope_files: list[str] | None = None,
    scope_uris: list[str] | None = None,
    form_values: dict[str, Any] | None = None,
    wait_for_confirmation: bool = False,
) -> dict[str, Any]:
    """
    Jedna ścieżka czatu: nlp2dsl (dopytywanie) → wykonanie Mullm → fallback RAG.
    """
    message = (message or "").strip()
    if form_values:
        extra = nlp.form_to_prompt(None, form_values)
        if extra:
            message = f"{message} {extra}".strip() if message else extra

    # Mullm-native intencje — przed nlp2dsl (unika „Nie rozpoznałem intencji”)
    if chat_service.is_file_list_intent(message):
        return await _mullm_file_list_turn(
            session_id=session_id,
            message=message,
            scope_files=scope_files,
            scope_uris=scope_uris,
        )

    if await nlp.health():
        return await _nlp2dsl_turn(
            session_id=session_id,
            message=message,
            nlp_conversation_id=nlp_conversation_id,
            scope_files=scope_files,
            scope_uris=scope_uris,
            wait_for_confirmation=wait_for_confirmation,
        )

    return await _fallback_turn(
        session_id=session_id,
        message=message,
        scope_files=scope_files,
        scope_uris=scope_uris,
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
    result = await ws.create_task_immediate(
        session_id,
        title=title,
        description=message,
        shell_command=shell,
        wait_for_confirmation=wait_for_confirmation,
    )
    return {
        "task": result,
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

    result = await ws.create_task_immediate(
        session_id,
        title=cfg.get("title") or message[:80],
        description=cfg.get("description") or message,
        shell_command=None,
        wait_for_confirmation=wait_for_confirmation,
    )
    return {
        "task": result,
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
