from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.events import (
    AgentHeartbeatReceived,
    AgentMarkedIdle,
    AgentRegistered,
    TaskAssignedToAgent,
)
from app.domain.value_objects import AgentId, AgentStatus, TaskId


@dataclass
class Agent:
    agent_id: AgentId
    agent_type: str
    capabilities: list[str] = field(default_factory=list)
    status: AgentStatus = AgentStatus.IDLE
    metadata: dict[str, Any] = field(default_factory=dict)
    current_task_id: TaskId | None = None
    heartbeat_at: datetime | None = None
    load_score: int = 0
    _events: list[Any] = field(default_factory=list)

    @classmethod
    def register(
        cls,
        agent_id: str,
        agent_type: str,
        capabilities: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> "Agent":
        agent = cls(
            agent_id=AgentId(agent_id),
            agent_type=agent_type,
            capabilities=capabilities,
            metadata=metadata or {},
        )
        agent._events.append(
            AgentRegistered(
                agent_id=agent.agent_id,
                agent_type=agent.agent_type,
                capabilities=agent.capabilities,
                metadata=agent.metadata,
            )
        )
        return agent

    def heartbeat(self, load_score: int = 0) -> None:
        self.load_score = load_score
        self.heartbeat_at = datetime.utcnow()
        self._events.append(
            AgentHeartbeatReceived(
                agent_id=self.agent_id,
                load_score=load_score,
                timestamp=self.heartbeat_at,
            )
        )

    def assign_task(self, task_id: TaskId) -> None:
        if self.status == AgentStatus.DISABLED:
            raise ValueError("Cannot assign task to disabled agent")
        self.status = AgentStatus.BUSY
        self.current_task_id = task_id
        self._events.append(TaskAssignedToAgent(agent_id=self.agent_id, task_id=task_id))

    def mark_idle(self) -> None:
        self.status = AgentStatus.IDLE
        self.current_task_id = None
        self._events.append(AgentMarkedIdle(agent_id=self.agent_id))

    def get_uncommitted_events(self) -> list[Any]:
        return self._events.copy()

    def mark_events_committed(self) -> None:
        self._events.clear()
