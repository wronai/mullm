import subprocess
import sys
import json
from pathlib import Path
from unittest.mock import patch

import pytest

def _run_shell_command(command: str, timeout_seconds: int = 120):
    root = Path(__file__).resolve().parents[1] / "agents" / "shell-agent"
    saved = {key: sys.modules[key] for key in list(sys.modules) if key == "app" or key.startswith("app.")}
    for key in saved:
        del sys.modules[key]
    sys.path.insert(0, str(root))
    try:
        from app.executor import run_shell_command as fn

        return fn(command, timeout_seconds=timeout_seconds)
    finally:
        for key in list(sys.modules):
            if key == "app" or key.startswith("app."):
                del sys.modules[key]
        sys.modules.update(saved)


def _shell_consumer_module():
    root = Path(__file__).resolve().parents[1] / "agents" / "shell-agent"
    saved = {key: sys.modules[key] for key in list(sys.modules) if key == "app" or key.startswith("app.")}
    for key in saved:
        del sys.modules[key]
    sys.path.insert(0, str(root))
    try:
        import app.nats_consumer as mod

        return mod
    finally:
        for key in list(sys.modules):
            if key == "app" or key.startswith("app."):
                del sys.modules[key]
        sys.modules.update(saved)


def test_run_shell_command_success():
    result = _run_shell_command("echo hello")
    assert result.ok
    assert "hello" in result.stdout


def test_run_shell_command_failure():
    result = _run_shell_command("exit 7")
    assert not result.ok
    assert result.exit_code == 7


def test_run_shell_command_timeout():
    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="sleep", timeout=1),
    ):
        result = _run_shell_command("sleep 999", timeout_seconds=1)
    assert result.timed_out
    assert not result.ok


@pytest.mark.asyncio
async def test_shell_agent_ignores_other_agent_assignment():
    mod = _shell_consumer_module()

    class Message:
        data = json.dumps(
            {
                "task_id": "task-1",
                "agent_id": "shell-agent-a",
                "command": "echo should-not-run",
            }
        ).encode()

    class Client:
        def __init__(self) -> None:
            self.published = []

        async def publish(self, subject, payload):
            self.published.append((subject, payload))

    agent = mod.ShellAgent(agent_id="shell-agent-b", nats_url="nats://test")
    agent.client = Client()

    with patch.object(mod, "run_shell_command") as run:
        await agent.handle_message(Message())

    run.assert_not_called()
    assert agent.client.published == []
