import pytest

from app import routing_policy as rp
from app.routing_policy import load_policy


def test_load_default_policy():
    policy = load_policy(reload=True)
    assert "rag_probe" in policy.ingress_order
    assert policy.ingress_order.index("rag_probe") < policy.ingress_order.index("rules")
    assert policy.agent_for_route("mullm_file_list") == "files_agent"


def test_session_agent_overrides_route():
    policy = load_policy(reload=True)
    assert policy.agent_for_route("mullm_shell", session_agent_id="ops_agent") == "ops_agent"


def test_mode_override_rag_only():
    policy = load_policy(reload=True)
    order = policy.ingress_for_mode("search_context")
    assert order == ["rag_answer"]


def test_policy_to_dict():
    d = load_policy(reload=True).to_dict()
    assert d["ingress_order"]
    assert d["agents"]["by_route"]["mullm_shell"] == "shell_agent"

