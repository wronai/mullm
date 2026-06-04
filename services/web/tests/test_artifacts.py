from app.workspace import (
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
