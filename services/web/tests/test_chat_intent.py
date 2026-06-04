from app.chat import (
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


def test_file_list_scope_usera():
    assert file_list_scope("lista plikow usera") == "user"
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


def test_format_user_scope_title():
    text = format_file_list_reply(
        {"resources": [], "rag_documents": [], "list_scope": "user"},
        scope_files=["upload.pdf"],
        list_scope="user",
    )
    assert "Pliki użytkownika" in text
    assert "upload.pdf" in text


def test_dedupe_rag_documents_by_uri():
    from app.chat import _dedupe_rows_by_uri

    rows = [
        {"uri": "mullm://localfs/rag-smoke.txt", "name": "RAG Smoke"},
        {"uri": "mullm://localfs/rag-smoke.txt", "name": "RAG Smoke"},
    ]
    assert len(_dedupe_rows_by_uri(rows)) == 1
