from app.agent_plugins.nlp2cmd_helpers import nlp2cmd_run_command, needs_run_wrapper, resolve_command_text
from app.routing_schemas import Nlp2CmdQueryResponse


def test_needs_run_wrapper_canvas_blueprint():
    parsed = Nlp2CmdQueryResponse(
        success=True,
        command="",
        confidence=0.95,
        domain="multi_step",
        intent="canvas_blueprint",
    )
    assert needs_run_wrapper(parsed)


def test_resolve_command_text_wraps_run_mode():
    parsed = Nlp2CmdQueryResponse(
        success=True,
        command="",
        confidence=0.95,
        domain="multi_step",
        intent="canvas_blueprint",
    )
    query = "wejdz na jspaint.app i narysuj biedronke"
    assert resolve_command_text(query, parsed) == nlp2cmd_run_command(query)


def test_resolve_command_text_keeps_shell_command():
    parsed = Nlp2CmdQueryResponse(
        success=True,
        command="ps aux",
        confidence=0.95,
        domain="shell",
        intent="list_processes",
    )
    assert resolve_command_text("pokaż procesy", parsed) == "ps aux"
