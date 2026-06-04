import pytest

from app import agent_workroom
from app.agent_workroom import _plan_steps, create_workroom, format_workroom_export
from app.chat import file_list_scope, is_file_list_intent
from app.resource_areas import agent_may_access, list_groups


def test_plan_includes_files_for_lista_plikow():
    steps = _plan_steps("lista plikow")
    agents = [s["agent"] for s in steps]
    assert "files_agent" in agents


def test_list_aplikow_usera_intent_and_scope():
    msg = "list aplikow usera"
    assert is_file_list_intent(msg)
    assert file_list_scope(msg) == "user"
    _assert_user_file_step(msg)


def _assert_user_file_step(msg: str) -> None:
    steps = _plan_steps(msg)
    file_step = next(s for s in steps if s["agent"] == "files_agent")
    assert file_step["list_scope"] == "user"
    assert "użytkownika" in file_step["label"].lower()


def test_workroom_export_contains_goal():
    s = create_workroom()
    s.goal = "list aplikow usera"
    s.agent_say("files_agent", "Files", "Pliki użytkownika")
    text = format_workroom_export(s)
    assert "list aplikow usera" in text
    assert "Pliki użytkownika" in text


def test_files_agent_may_list_rag():
    d = agent_may_access("files_agent", "mullm:rag", "list")
    assert d["decision"] in ("allow", "approval")


def test_mail_agent_denied_rag():
    d = agent_may_access("mail_agent", "mullm:rag", "list")
    assert d["decision"] == "deny"


def test_groups_nonempty():
    assert len(list_groups()) >= 2


def test_workroom_session_dict():
    s = create_workroom()
    d = s.to_dict()
    assert d["workroom_id"]
    assert d["status"] == "idle"


@pytest.mark.asyncio
async def test_run_workroom_file_list_step(monkeypatch):
    async def fake_file_list(goal, *, scope_files, scope_uris):
        return "Lista plików testowa", {"resources": [], "rag_documents": []}, "all"

    monkeypatch.setattr(agent_workroom, "_build_file_list_for_goal", fake_file_list)
    s = create_workroom()

    out = await agent_workroom.run_workroom(s.workroom_id, "lista plikow")

    assert out["ok"] is True
    assert out["status"] == "done"
    assert "Lista plików testowa" in out["result_summary"]
    assert any(e["kind"] == "result" for e in out["ledger"])
