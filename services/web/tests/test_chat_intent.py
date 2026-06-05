import pytest

from app.chat import (
    build_file_list_artifact,
    file_list_scope,
    filter_file_inventory,
    format_file_list_reply,
    is_file_list_intent,
)


def test_file_list_intent_pl():
    assert is_file_list_intent("lista plikow")
    assert is_file_list_intent("pokaż pliki w scope")
    assert is_file_list_intent("liat plikoq")
    assert not is_file_list_intent("napraw błąd RAG")


def test_format_file_list():
    text = format_file_list_reply(
        {
            "resources": [{"name": "a.txt", "uri": "mullm://x", "status": "ready"}],
            "rag_documents": [{"name": "a.txt", "uri": "mullm://x", "status": "indexed", "chunk_count": 3}],
        },
        scope_files=["upload.pdf"],
    )
    assert "a.txt" in text
    assert "upload.pdf" in text
    assert "Indeks RAG: 1" in text


def test_file_list_intent_aplikow_typo():
    assert is_file_list_intent("list aplikow usera")


def test_file_list_intent_en_and_pikow():
    assert is_file_list_intent("lista user files")
    assert file_list_scope("lista user files") == "user"
    assert is_file_list_intent("lista pikow usera")
    assert file_list_scope("lista pikow usera") == "user"


def test_file_list_scope_usera():
    assert file_list_scope("lista plikow usera") == "user"
    assert file_list_scope("list aplikow usera") == "user"
    assert file_list_scope("lista plików systemu") == "system"
    assert file_list_scope("lista plikow") == "all"


def test_filter_user_files():
    inv = filter_file_inventory(
        {
            "resources": [
                {"name": "a", "uri": "mullm://localfs/a.txt", "status": "ok"},
                {"name": "t", "uri": "mullm://ticket/x", "status": "ok"},
            ],
            "rag_documents": [],
        },
        "user",
    )
    assert len(inv["resources"]) == 1
    assert inv["resources"][0]["uri"].startswith("mullm://localfs")


def test_file_list_artifact():
    art = build_file_list_artifact(
        "body",
        {"list_scope": "user", "resources": []},
        session_id="f47293b1-276c-48ed-972f-0fc030969fec",
        list_scope="user",
    )
    assert art["kind"] == "file_list"
    assert art["filename"].endswith(".txt")
    assert "user" in art["filename"]
    assert art["text"] == "body"


def test_format_user_scope_title():
    text = format_file_list_reply(
        {"resources": [], "rag_documents": [], "list_scope": "user"},
        scope_files=["upload.pdf"],
        scope_uris=["mullm://ticket/abc"],
        list_scope="user",
    )
    assert "Pliki użytkownika" in text
    assert "upload.pdf" in text
    assert "tickety shell" in text
    assert "panelu ◎" in text
    assert "mullm://ticket/abc" not in text


def test_dedupe_rag_documents_by_uri():
    from app.chat import _dedupe_rows_by_uri

    rows = [
        {"uri": "mullm://localfs/rag-smoke.txt", "name": "RAG Smoke"},
        {"uri": "mullm://localfs/rag-smoke.txt", "name": "RAG Smoke"},
    ]
    assert len(_dedupe_rows_by_uri(rows)) == 1


@pytest.mark.asyncio
async def test_handle_message_file_list_builds_artifact(monkeypatch):
    import app.chat as chat

    async def fake_inventory():
        return {
            "resources": [
                {"name": "upload.pdf", "uri": "mullm://localfs/upload.pdf", "status": "ready"}
            ],
            "rag_documents": [],
            "errors": [],
        }

    monkeypatch.setattr(chat, "fetch_file_inventory", fake_inventory)

    out = await chat.handle_message(
        session_id="test-file-list",
        message="lista plikow usera",
        use_rag=True,
        scope_files=["upload.pdf"],
    )

    assert out["intent"] == "file_list"
    assert out["artifact"]["kind"] == "file_list"
    assert "upload.pdf" in out["reply"]
