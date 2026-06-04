from app.workspace import (
    _format_export_text,
    artifact_summaries,
    format_chat_export_text,
    get_artifact,
    get_or_create,
    register_artifact,
)


def test_register_and_get_artifact():
    session = get_or_create("sess-artifact-1")
    session.artifacts.clear()
    art = _register_user_file_list_artifact(session)
    assert art["artifact_id"]
    assert art["title"] == "Lista plików (user)"
    _assert_single_artifact_summary(session)
    _assert_artifact_text(session, art["artifact_id"], "hello")


def _register_user_file_list_artifact(session):
    return register_artifact(
        session,
        {
            "kind": "file_list",
            "list_scope": "user",
            "filename": "lista.txt",
            "text": "hello",
            "json": {"resources": []},
        },
        source_message="lista plikow usera",
    )


def _assert_single_artifact_summary(session) -> None:
    summaries = artifact_summaries(session)
    assert len(summaries) == 1
    assert summaries[0]["has_json"] is True


def _assert_artifact_text(session, artifact_id: str, expected: str) -> None:
    full = get_artifact(session.session_id, artifact_id)
    assert full is not None
    assert full["text"] == expected


def test_format_export_text_keeps_core_sections():
    text = _format_export_text(
        {
            "generated_at": "2026-06-04T00:00:00+00:00",
            "correlation_id": "corr-1",
            "session": {
                "context": {"ticket_id": "ABC-1", "file_names": ["a.txt"]},
                "chat_history": [{"role": "user", "content": "lista plikow"}],
                "events": [{"type": "FileListReturned", "summary": "Lista"}],
            },
            "inventory": {
                "resources": [{"name": "a.txt", "uri": "mullm://localfs/a.txt", "status": "ready"}],
                "rag_documents": [],
            },
        }
    )

    assert "## Kontekst" in text
    assert "## NFO" in text
    assert "ABC-1" in text
    assert "## Historia chatu" in text
    assert "## Zdarzenia sesji" in text


def test_format_export_text_uses_log_limit_for_verbose_sections():
    text = _format_export_text(
        {
            "generated_at": "2026-06-04T00:00:00+00:00",
            "correlation_id": "corr-verbose",
            "log_limit": 2,
            "session": {
                "context": {},
                "chat_history": [],
                "events": [
                    {"type": "E1", "summary": "one"},
                    {"type": "E2", "summary": "two"},
                    {"type": "E3", "summary": "three"},
                ],
            },
            "rag_snapshots": [
                {"correlation_id": "corr-verbose", "created_at": "t1", "status": "s1"},
                {"correlation_id": "corr-verbose", "created_at": "t2", "status": "s2"},
                {"correlation_id": "corr-verbose", "created_at": "t3", "status": "s3"},
            ],
            "operational_feed": [
                {"occurred_at": "2026-06-04T00:00:01", "event_type": "A", "summary": "a"},
                {"occurred_at": "2026-06-04T00:00:02", "event_type": "B", "summary": "b"},
                {"occurred_at": "2026-06-04T00:00:03", "event_type": "C", "summary": "c"},
            ],
        }
    )

    assert "E1: one" not in text
    assert "E2: two" in text
    assert "E3: three" in text
    assert "t1 s1" in text
    assert "t2 s2" in text
    assert "t3 s3" not in text
    assert " A — a" in text
    assert " B — b" in text
    assert " C — c" not in text


def test_format_chat_export_includes_routing():
    session = get_or_create("sess-chat-export")
    session.events.clear()
    routing = {
        "route": "mullm_file_list",
        "handler": "conductor._mullm_file_list_turn",
        "confidence": 0.92,
        "reason_codes": ["intent_file_list"],
        "router_mode": "rules",
    }
    from app import chat as chat_service

    chat_service._sessions[session.session_id] = [
        {"role": "user", "content": "lista plikow usera"},
        {"role": "assistant", "content": "Pliki…", "routing": routing},
    ]
    text = format_chat_export_text(session)
    assert "## Ty" in text
    assert "## AI" in text
    assert "mullm_file_list" in text
    assert "intent_file_list" in text
    assert "## Routing trace" in text


def test_format_export_includes_routing_trace():
    routing = {
        "route": "mullm_file_list",
        "handler": "conductor._mullm_file_list_turn",
        "intent": "file_list",
        "confidence": 0.92,
        "reason_codes": ["intent_file_list", "scope_user"],
        "fallback_route": "nlp2dsl",
        "timing_ms": 1.1,
        "router_mode": "rules",
        "candidate_routes": [{"route": "mullm_file_list", "confidence": 0.92}],
    }
    text = _format_export_text(
        {
            "generated_at": "2026-06-04T00:00:00+00:00",
            "correlation_id": "corr-r",
            "session": {
                "context": {},
                "chat_history": [
                    {"role": "user", "content": "lista plikow usera"},
                    {"role": "assistant", "content": "Pliki…", "routing": routing},
                ],
                "events": [
                    {
                        "type": "RouteDecided",
                        "summary": "mullm_file_list → conductor",
                        "routing": routing,
                        "outcome": "succeeded",
                    },
                ],
            },
        }
    )
    assert "## Routing trace" in text
    assert "mullm_file_list" in text
    assert "intent_file_list" in text
    assert "(route: mullm_file_list" in text
    assert "if_not_chosen: nlp2dsl" in text


def test_format_routing_line_nlp2dsl_skipped():
    from app.workspace import _format_routing_line

    line = _format_routing_line(
        {
            "route": "mullm_file_list",
            "handler": "conductor._mullm_file_list_turn",
            "confidence": 0.92,
            "reason_codes": ["intent_file_list"],
            "fallback_route": "nlp2dsl",
            "nlp2dsl_skipped": True,
            "router_mode": "rules",
        }
    )
    assert "nlp2dsl: skipped" in line
    assert "if_not_chosen: nlp2dsl" in line
    assert "fallback: nlp2dsl" not in line
