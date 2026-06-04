import pytest

from app import prompt_router as pr


@pytest.mark.parametrize(
    "msg,scope",
    [
        ("lista plikow usera", "user"),
        ("lista user files", "user"),
        ("lista pikow usera", "user"),
    ],
)
def test_file_list_routes(msg, scope):
    d = pr.decide_route_rules(msg)
    assert d.route == "mullm_file_list"
    assert d.list_scope == scope
    assert "intent_file_list" in d.reason_codes
    assert d.candidate_routes
    assert d.handler == "conductor._mullm_file_list_turn"


def test_shell_route():
    d = pr.decide_route_rules("run ls -la")
    assert d.route == "mullm_shell"
    assert d.fallback_route == "nlp2dsl"


def test_discuss_defaults_nlp2dsl():
    d = pr.decide_route_rules("wyślij fakturę do klienta")
    assert d.route == "nlp2dsl"
    assert d.fallback_route == "rag"
    assert len(d.candidate_routes) >= 2


def test_search_context_rag():
    d = pr.decide_route_rules("co w pliku?", chat_mode="search_context")
    assert d.route == "rag"
    assert d.policy_flags.get("chat_mode") == "search_context"


def test_route_decision_to_dict():
    d = pr.decide_route_rules("lista plikow")
    payload = d.to_dict()
    for key in (
        "route",
        "handler",
        "intent",
        "confidence",
        "reason_codes",
        "candidate_routes",
        "policy_flags",
        "timing_ms",
    ):
        assert key in payload


@pytest.mark.asyncio
async def test_decide_route_sets_timing():
    d = await pr.decide_route("lista user files")
    assert d.timing_ms >= 0
    assert d.router_mode in ("rules", "llm")
