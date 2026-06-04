from __future__ import annotations

import asyncio
import os

from app.nats_consumer import ShellAgent


NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")
AGENT_ID = os.getenv("AGENT_ID", "shell-agent-a")
TIMEOUT_SECONDS = int(os.getenv("SHELL_TIMEOUT_SECONDS", "120"))


async def main() -> None:
    agent = ShellAgent(
        agent_id=AGENT_ID,
        nats_url=NATS_URL,
        timeout_seconds=TIMEOUT_SECONDS,
    )
    await agent.run()
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
