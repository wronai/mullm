from app.agent_workroom import _plan_steps, create_workroom
from app.resource_areas import agent_may_access, list_groups


def test_plan_includes_files_for_lista_plikow():
    steps = _plan_steps("lista plikow")
    agents = [s["agent"] for s in steps]
    assert "files_agent" in agents


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
