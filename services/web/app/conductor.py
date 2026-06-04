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
        if not nlp_conversation_id:
            resp = await nlp.chat_start(message)
        else:
            resp = await nlp.chat_message(nlp_conversation_id, message)
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

    out: dict[str, Any] = {
        "nlp2dsl_conversation_id": cid,
        "nlp2dsl_status": status,
        "clarify": None,
        "task": None,
    }

    if status == "in_progress":
        out["reply"] = assistant or "Potrzebuję jeszcze kilku informacji — uzupełnij poniżej."
        out["clarify"] = {
            "conversation_id": cid,
            "missing": resp.get("missing") or [],
            "form": resp.get("form"),
            "hint": "Odpowiedz w polu lub wypełnij formularz i wyślij.",
        }
        chat_service._append(session_id, "user", message)
        chat_service._append(session_id, "assistant", out["reply"], clarify=True)
        out["history"] = chat_service.get_history(session_id)
        return out

    if status == "ready":
        dsl = resp.get("dsl")
        action = nlp.primary_action(dsl)
        cfg = nlp.step_config(dsl)

        if action == "system_file_list":
            inv = await chat_service.fetch_file_inventory()
            reply = chat_service.format_file_list_reply(
                inv, scope_files=scope_files, scope_uris=scope_uris
            )
            out["reply"] = reply
            out["executed"] = "mullm_file_list"
        elif action == "mullm_shell_task":
            shell = cfg.get("shell_command") or _extract_shell(message)
            title = cfg.get("title") or message[:80]
            if not shell:
                out["reply"] = "Podaj polecenie shell (np. `run ls -la`)."
                out["clarify"] = {
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
                }
            else:
                from app import workspace as ws

                result = await ws.create_task_immediate(
                    session_id,
                    title=title,
                    description=message,
                    shell_command=shell,
                    wait_for_confirmation=wait_for_confirmation,
                )
                out["task"] = result
                tid = result.get("task_id")
                if result.get("ok"):
                    out["reply"] = (
                        f"Ticket `{tid}` w kolejce — potwierdź na liście (◎)."
                        if wait_for_confirmation
                        else f"Uruchomiono ticket `{tid}` · `{shell}`"
                    )
                else:
                    out["reply"] = f"Nie udało się: {result.get('error')}"
                out["executed"] = "mullm_shell"
        elif action == "mullm_create_ticket":
            from app import workspace as ws

            title = cfg.get("title") or message[:80]
            result = await ws.create_task_immediate(
                session_id,
                title=title,
                description=cfg.get("description") or message,
                shell_command=None,
                wait_for_confirmation=wait_for_confirmation,
            )
            out["task"] = result
            tid = result.get("task_id")
            if result.get("ok"):
                out["reply"] = (
                    f"Ticket `{tid}` w kolejce — potwierdź na liście (◎)."
                    if wait_for_confirmation
                    else f"Utworzono i uruchomiono ticket `{tid}`."
                )
            else:
                out["reply"] = f"Nie udało się: {result.get('error')}"
            out["executed"] = "mullm_ticket"
        else:
            out["reply"] = (
                assistant
                + "\n\n(Workflow gotowy — akcja poza Mullm; uruchom w nlp2dsl lub doprecyzuj.)"
            )
            out["dsl"] = dsl

        chat_service._append(session_id, "user", message)
        chat_service._append(session_id, "assistant", out["reply"])
        out["history"] = chat_service.get_history(session_id)
        out["correlation_id"] = session_id
        return out

    out["reply"] = assistant or "Rozmowa zakończona."
    chat_service._append(session_id, "user", message)
    chat_service._append(session_id, "assistant", out["reply"])
    out["history"] = chat_service.get_history(session_id)
    return out


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
