from app.workspace import (
    _format_export_text,
    artifact_summaries,
    get_artifact,
    get_or_create,
    register_artifact,
)


def test_register_and_get_artifact():
    session = get_or_create("sess-artifact-1")
    session.artifacts.clear()
    art = register_artifact(
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
    assert art["artifact_id"]
    assert art["title"] == "Lista plików (user)"
    summaries = artifact_summaries(session)
    assert len(summaries) == 1
    assert summaries[0]["has_json"] is True
    full = get_artifact(session.session_id, art["artifact_id"])
    assert full is not None
    assert full["text"] == "hello"


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
    assert "ABC-1" in text
    assert "## Historia chatu" in text
    assert "## Zdarzenia sesji" in text
