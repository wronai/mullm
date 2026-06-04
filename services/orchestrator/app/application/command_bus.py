from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.domain.aggregates.agent import Agent
from app.domain.aggregates.approval import Approval
from app.domain.aggregates.plugin import Plugin
from app.domain.aggregates.task import Task
from app.domain.aggregates.workflow import Workflow
from app.domain.events import AgentMarkedIdle, TaskAssignedToAgent
from app.domain.aggregates.plugin import PluginStatus
from app.domain.value_objects import (
    AgentId,
    ApprovalId,
    ExecutionMode,
    PluginId,
    Priority,
    TaskId,
    WorkflowId,
    WorkflowStatus,
)


class CommandBus:
    def __init__(self, event_store, message_bus=None):
        self.event_store = event_store
        self.message_bus = message_bus

    async def handle(
        self,
        *,
        command_type: str,
        command_id: str | None = None,
        data: dict[str, Any] | None = None,
        correlation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        command_id = command_id or str(uuid4())
        data = data or {}

        if command_type == "CreateTask":
            return await self._create_task(command_id, data, correlation_id, metadata)
        if command_type in {"AssignTask", "AssignTaskToAgent"}:
            return await self._assign_task(command_id, data, correlation_id, metadata)
        if command_type in {"StartTask", "StartTaskExecution"}:
            return await self._start_task(command_id, data, correlation_id, metadata)
        if command_type == "CompleteTask":
            return await self._complete_task(command_id, data, correlation_id, metadata)
        if command_type == "FailTask":
            return await self._fail_task(command_id, data, correlation_id, metadata)
        if command_type == "RegisterAgent":
            return await self._register_agent(command_id, data, correlation_id, metadata)
        if command_type == "AgentHeartbeat":
            return await self._agent_heartbeat(command_id, data, correlation_id, metadata)
        if command_type == "StartWorkflow":
            return await self._start_workflow(command_id, data, correlation_id, metadata)
        if command_type == "ProposeWorkflowVersion":
            return await self._propose_workflow_version(
                command_id, data, correlation_id, metadata
            )
        if command_type == "ValidateWorkflowVersion":
            return await self._validate_workflow_version(
                command_id, data, correlation_id, metadata
            )
        if command_type == "ApproveWorkflowVersion":
            return await self._approve_workflow_version(
                command_id, data, correlation_id, metadata
            )
        if command_type == "ActivateWorkflowVersion":
            return await self._activate_workflow_version(
                command_id, data, correlation_id, metadata
            )
        if command_type == "RollbackWorkflowVersion":
            return await self._rollback_workflow_version(
                command_id, data, correlation_id, metadata
            )
        if command_type == "ProposePlugin":
            return await self._propose_plugin(command_id, data, correlation_id, metadata)
        if command_type == "ValidatePlugin":
            return await self._validate_plugin(command_id, data, correlation_id, metadata)
        if command_type == "InstallPlugin":
            return await self._install_plugin(command_id, data, correlation_id, metadata)
        if command_type == "ActivatePlugin":
            return await self._activate_plugin(command_id, data, correlation_id, metadata)
        if command_type == "RollbackPlugin":
            return await self._rollback_plugin(command_id, data, correlation_id, metadata)
        if command_type == "CreateApprovalRequest":
            return await self._create_approval(command_id, data, correlation_id, metadata)
        if command_type == "ApproveRequest":
            return await self._approve_request(command_id, data, correlation_id, metadata)
        if command_type == "RejectRequest":
            return await self._reject_request(command_id, data, correlation_id, metadata)
        if command_type == "ExpireApproval":
            return await self._expire_approval(command_id, data, correlation_id, metadata)

        raise ValueError(f"Unsupported command type: {command_type}")

    async def handle_envelope(self, envelope: dict[str, Any]) -> dict[str, Any]:
        return await self.handle(
            command_type=envelope["command_type"],
            command_id=envelope.get("command_id"),
            data=envelope.get("payload") or {},
            correlation_id=envelope.get("correlation_id"),
            metadata={
                "actor": envelope.get("actor") or {},
                **(envelope.get("metadata") or {}),
            },
        )

    async def _create_task(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        agent_id = data.get("agent_id")
        task = Task.create(
            title=data["title"],
            description=data.get("description"),
            agent_id=AgentId(agent_id) if agent_id else None,
            priority=Priority.from_value(data.get("priority")),
            metadata=data.get("metadata") or {},
            execution_mode=ExecutionMode.from_value(data.get("execution_mode")),
            required_capabilities=data.get("required_capabilities") or [],
        )
        if agent_id:
            task.assign_to_agent(AgentId(agent_id))

        records = await self._append_and_publish(
            "task",
            str(task.task_id),
            task.get_uncommitted_events(),
            command_id=command_id,
            correlation_id=correlation_id,
            metadata=metadata,
        )
        task.mark_events_committed()
        return self._result(str(task.task_id), records)

    async def _assign_task(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        task_id = data["task_id"]
        agent_id = data["agent_id"]
        task = await self._load_task(task_id)
        task.assign_to_agent(AgentId(agent_id))

        task_records = await self._append_and_publish(
            "task",
            task_id,
            task.get_uncommitted_events(),
            command_id=command_id,
            correlation_id=correlation_id,
            metadata=metadata,
        )
        task.mark_events_committed()

        agent_records = await self._append_and_publish(
            "agent",
            agent_id,
            [TaskAssignedToAgent(agent_id=AgentId(agent_id), task_id=TaskId(task_id))],
            command_id=command_id,
            correlation_id=correlation_id,
            metadata=metadata,
        )

        shell_command = data.get("command") or data.get("shell_command")
        if shell_command:
            await self._publish(
                "task.assigned.shell",
                {"task_id": task_id, "agent_id": agent_id, "command": shell_command},
            )

        return self._result(task_id, [*task_records, *agent_records])

    async def _start_task(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        task_id = data["task_id"]
        task = await self._load_task(task_id)
        task.start()
        records = await self._append_and_publish(
            "task",
            task_id,
            task.get_uncommitted_events(),
            command_id=command_id,
            correlation_id=correlation_id,
            metadata=metadata,
        )
        task.mark_events_committed()
        return self._result(task_id, records)

    async def _complete_task(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        task_id = data["task_id"]
        task = await self._load_task(task_id)
        task.complete(result=data.get("result") or {})
        records = await self._append_and_publish(
            "task",
            task_id,
            task.get_uncommitted_events(),
            command_id=command_id,
            correlation_id=correlation_id,
            metadata=metadata,
        )
        task.mark_events_committed()

        if task.agent_id:
            idle_records = await self._append_and_publish(
                "agent",
                str(task.agent_id),
                [AgentMarkedIdle(agent_id=task.agent_id)],
                command_id=command_id,
                correlation_id=correlation_id,
                metadata=metadata,
            )
            records.extend(idle_records)

        return self._result(task_id, records)

    async def _fail_task(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        task_id = data["task_id"]
        task = await self._load_task(task_id)
        task.fail(error=data["error"])
        records = await self._append_and_publish(
            "task",
            task_id,
            task.get_uncommitted_events(),
            command_id=command_id,
            correlation_id=correlation_id,
            metadata=metadata,
        )
        task.mark_events_committed()

        if task.agent_id:
            idle_records = await self._append_and_publish(
                "agent",
                str(task.agent_id),
                [AgentMarkedIdle(agent_id=task.agent_id)],
                command_id=command_id,
                correlation_id=correlation_id,
                metadata=metadata,
            )
            records.extend(idle_records)

        return self._result(task_id, records)

    async def _register_agent(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        agent = Agent.register(
            agent_id=data["agent_id"],
            agent_type=data["agent_type"],
            capabilities=data.get("capabilities") or [],
            metadata=data.get("metadata") or {},
        )
        records = await self._append_and_publish(
            "agent",
            str(agent.agent_id),
            agent.get_uncommitted_events(),
            command_id=command_id,
            correlation_id=correlation_id,
            metadata=metadata,
        )
        agent.mark_events_committed()
        return self._result(str(agent.agent_id), records)

    async def _agent_heartbeat(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        agent = Agent(
            agent_id=AgentId(data["agent_id"]),
            agent_type=data.get("agent_type", "shell"),
            capabilities=data.get("capabilities") or [],
        )
        agent.heartbeat(load_score=int(data.get("load_score", 0)))
        records = await self._append_and_publish(
            "agent",
            str(agent.agent_id),
            agent.get_uncommitted_events(),
            command_id=command_id,
            correlation_id=correlation_id,
            metadata=metadata,
        )
        agent.mark_events_committed()
        return self._result(str(agent.agent_id), records)

    async def _start_workflow(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        workflow = Workflow.start(
            workflow_id=data["workflow_id"],
            input_data=data.get("input_data") or {},
            agent_assignments=data.get("agent_assignments") or {},
        )
        records = await self._append_and_publish(
            "workflow",
            str(workflow.workflow_id),
            workflow.get_uncommitted_events(),
            command_id=command_id,
            correlation_id=correlation_id,
            metadata=metadata,
        )
        workflow.mark_events_committed()
        return self._result(str(workflow.workflow_id), records)

    async def _propose_workflow_version(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        workflow = Workflow.propose_version(
            workflow_id=data["workflow_id"],
            version=int(data["version"]),
            definition=data.get("definition") or {},
        )
        return await self._persist_workflow(
            workflow, command_id, correlation_id, metadata
        )

    async def _validate_workflow_version(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        workflow = await self._load_workflow(data["workflow_id"])
        workflow.validate_version()
        return await self._persist_workflow(
            workflow, command_id, correlation_id, metadata
        )

    async def _approve_workflow_version(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        workflow = await self._load_workflow(data["workflow_id"])
        workflow.approve_version(data.get("approved_by", "system"))
        return await self._persist_workflow(
            workflow, command_id, correlation_id, metadata
        )

    async def _activate_workflow_version(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        workflow = await self._load_workflow(data["workflow_id"])
        workflow.activate_version()
        return await self._persist_workflow(
            workflow, command_id, correlation_id, metadata
        )

    async def _rollback_workflow_version(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        workflow = await self._load_workflow(data["workflow_id"])
        workflow.rollback_version(data.get("reason", ""))
        return await self._persist_workflow(
            workflow, command_id, correlation_id, metadata
        )

    async def _propose_plugin(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        plugin = Plugin.propose(
            plugin_id=data["plugin_id"],
            version=data["version"],
            capabilities=data.get("capabilities") or [],
            manifest=data.get("manifest") or {},
        )
        return await self._persist_plugin(plugin, command_id, correlation_id, metadata)

    async def _validate_plugin(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        plugin = await self._load_plugin(data["plugin_id"])
        plugin.validate()
        return await self._persist_plugin(plugin, command_id, correlation_id, metadata)

    async def _install_plugin(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        plugin = await self._load_plugin(data["plugin_id"])
        plugin.install()
        return await self._persist_plugin(plugin, command_id, correlation_id, metadata)

    async def _activate_plugin(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        plugin = await self._load_plugin(data["plugin_id"])
        plugin.activate()
        return await self._persist_plugin(plugin, command_id, correlation_id, metadata)

    async def _rollback_plugin(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        plugin = await self._load_plugin(data["plugin_id"])
        plugin.rollback(data.get("reason", ""))
        return await self._persist_plugin(plugin, command_id, correlation_id, metadata)

    async def _create_approval(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        approval = Approval.create_request(
            action_type=data["action_type"],
            target_id=data["target_id"],
            risk_level=data.get("risk_level", "medium"),
            requested_by=data["requested_by"],
            approval_id=data.get("approval_id"),
        )
        return await self._persist_approval(
            approval, command_id, correlation_id, metadata
        )

    async def _approve_request(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        approval = await self._load_approval(data["approval_id"])
        approval.approve(data["approved_by"])
        return await self._persist_approval(
            approval, command_id, correlation_id, metadata
        )

    async def _reject_request(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        approval = await self._load_approval(data["approval_id"])
        approval.reject(data["rejected_by"], data.get("reason", ""))
        return await self._persist_approval(
            approval, command_id, correlation_id, metadata
        )

    async def _expire_approval(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        approval = await self._load_approval(data["approval_id"])
        approval.expire()
        return await self._persist_approval(
            approval, command_id, correlation_id, metadata
        )

    async def _persist_workflow(
        self,
        workflow: Workflow,
        command_id: str,
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        records = await self._append_and_publish(
            "workflow",
            str(workflow.workflow_id),
            workflow.get_uncommitted_events(),
            command_id=command_id,
            correlation_id=correlation_id,
            metadata=metadata,
        )
        workflow.mark_events_committed()
        return self._result(str(workflow.workflow_id), records)

    async def _persist_plugin(
        self,
        plugin: Plugin,
        command_id: str,
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        records = await self._append_and_publish(
            "plugin",
            str(plugin.plugin_id),
            plugin.get_uncommitted_events(),
            command_id=command_id,
            correlation_id=correlation_id,
            metadata=metadata,
        )
        plugin.mark_events_committed()
        return self._result(str(plugin.plugin_id), records)

    async def _persist_approval(
        self,
        approval: Approval,
        command_id: str,
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        records = await self._append_and_publish(
            "approval",
            str(approval.approval_id),
            approval.get_uncommitted_events(),
            command_id=command_id,
            correlation_id=correlation_id,
            metadata=metadata,
        )
        approval.mark_events_committed()
        return self._result(str(approval.approval_id), records)

    async def _load_workflow(self, workflow_id: str) -> Workflow:
        events = await self.event_store.get_events_for_aggregate("workflow", workflow_id)
        if not events:
            raise ValueError(f"Workflow not found: {workflow_id}")
        last = events[-1].data
        workflow = Workflow(
            workflow_id=WorkflowId(workflow_id),
            version=int(last.get("version", 1)),
        )
        status = last.get("status", "proposed")
        for candidate in WorkflowStatus:
            if candidate.value == status:
                workflow.status = candidate
                break
        workflow.definition = last.get("definition") or {}
        return workflow

    async def _load_plugin(self, plugin_id: str) -> Plugin:
        events = await self.event_store.get_events_for_aggregate("plugin", plugin_id)
        if not events:
            raise ValueError(f"Plugin not found: {plugin_id}")
        last = events[-1].data
        plugin = Plugin(
            plugin_id=PluginId(plugin_id),
            version=last.get("version", "0.1.0"),
            capabilities=last.get("capabilities") or [],
            manifest=last.get("manifest") or {},
            status=last.get("status", PluginStatus.PROPOSED),
        )
        return plugin

    async def _load_approval(self, approval_id: str) -> Approval:
        events = await self.event_store.get_events_for_aggregate("approval", approval_id)
        if not events:
            raise ValueError(f"Approval not found: {approval_id}")
        first = events[0].data
        last = events[-1].data
        approval = Approval(
            approval_id=ApprovalId(approval_id),
            action_type=first.get("action_type", ""),
            target_id=first.get("target_id", ""),
            risk_level=first.get("risk_level", "medium"),
            requested_by=first.get("requested_by", ""),
            status=last.get("status", "pending"),
        )
        return approval

    async def _load_task(self, task_id: str) -> Task:
        events = await self.event_store.get_events_for_aggregate("task", task_id)
        if not events:
            raise ValueError(f"Task not found: {task_id}")
        return Task.from_events(events)

    async def _append_and_publish(
        self,
        aggregate_type: str,
        aggregate_id: str,
        events: list[Any],
        *,
        command_id: str,
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> list[Any]:
        records = await self.event_store.append(
            aggregate_type,
            aggregate_id,
            events,
            causation_id=command_id,
            correlation_id=correlation_id,
            metadata=metadata or {},
        )
        for record in records:
            message = record.to_message() if hasattr(record, "to_message") else record
            await self._publish("mullm.events", message)
        return records

    async def _publish(self, subject: str, payload: dict[str, Any]) -> None:
        if self.message_bus:
            await self.message_bus.publish(subject, payload)

    def _result(self, aggregate_id: str, records: list[Any]) -> dict[str, Any]:
        return {
            "aggregate_id": aggregate_id,
            "events": [
                record.to_message() if hasattr(record, "to_message") else record
                for record in records
            ],
        }
