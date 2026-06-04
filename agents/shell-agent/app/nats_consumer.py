from __future__ import annotations

from typing import Any
import json
import logging

from app.executor import run_shell_command

try:
    from nats.aio.client import Client as NATS
except ModuleNotFoundError:  # pragma: no cover
    NATS = None


logger = logging.getLogger(__name__)


class ShellAgent:
    def __init__(self, *, agent_id: str, nats_url: str, timeout_seconds: int = 120):
        self.agent_id = agent_id
        self.nats_url = nats_url
        self.timeout_seconds = timeout_seconds
        self.client: Any = None

    async def run(self) -> None:
        if NATS is None:
            raise RuntimeError("nats-py is required to run the shell agent")

        self.client = NATS()
        await self.client.connect(servers=[self.nats_url])
        await self.client.subscribe("task.assigned.shell", cb=self.handle_message)
        logger.info("Shell agent %s subscribed to task.assigned.shell", self.agent_id)

    async def handle_message(self, msg) -> None:
        payload = json.loads(msg.data.decode())
        assigned_agent = payload.get("agent_id")
        if assigned_agent and assigned_agent != self.agent_id:
            return

        result = run_shell_command(payload["command"], timeout_seconds=self.timeout_seconds)
        event = {
            "agent_id": self.agent_id,
            "task_id": payload["task_id"],
            **result.to_dict(),
        }
        subject = "task.shell.completed" if result.ok else "task.shell.failed"
        await self.client.publish(subject, json.dumps(event).encode())
