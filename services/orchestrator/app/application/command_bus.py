from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.domain.aggregates.agent import Agent
from app.domain.aggregates.approval import Approval
from app.domain.aggregates.plugin import Plugin
from app.domain.aggregates.task import Task
from app.domain.aggregates.resource import Resource
from app.domain.aggregates.workflow import Workflow
from app.access.uri import parse_uri
from app.domain.events import (
    AgentMarkedIdle,
    ChangeProposed,
    TaskAssignedToAgent,
)
from app.evolution.policy_engine import PolicyViolation
from app.application.sagas.approval_gate import ensure_approval, follow_up_after_grant
from app.application.sagas.task_routing import maybe_auto_assign
from app.domain.aggregates.plugin import PluginStatus
from app.domain.value_objects import (
    AgentId,
    ApprovalId,
    ExecutionMode,
    PluginId,
    Priority,
    ResourceId,
    TaskId,
    WorkflowId,
    WorkflowStatus,
)


class CommandBus:
    def __init__(
        self,
        event_store,
        message_bus=None,
        *,
        postgres=None,
        policy_engine=None,
        evaluation=None,
        experiments=None,
        transport=None,
        rag_indexer=None,
        environment: str = "dev",
    ):
        self.event_store = event_store
        self.message_bus = message_bus
        self.postgres = postgres
        self.policy_engine = policy_engine
        self.evaluation = evaluation
        self.experiments = experiments
        self.transport = transport
        self.rag_indexer = rag_indexer
        self.environment = environment

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
        if command_type == "ShadowWorkflowVersion":
            return await self._shadow_workflow_version(
                command_id, data, correlation_id, metadata
            )
        if command_type == "ProposeChange":
            return await self._propose_change(command_id, data, correlation_id, metadata)
        if command_type == "RegisterResource":
            return await self._register_resource(command_id, data, correlation_id, metadata)
        if command_type == "RequestTransfer":
            return await self._request_transfer(command_id, data, correlation_id, metadata)

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
        result = self._result(str(task.task_id), records)
        assign_result = await maybe_auto_assign(
            self,
            task_id=str(task.task_id),
            data=data,
            command_id=command_id,
            correlation_id=correlation_id,
            metadata=metadata,
        )
        if assign_result:
            result["auto_assign"] = assign_result
        return result

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
        await self._record_task_outcome(task, success=True, metadata=metadata)
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
        await self._record_task_outcome(
            task,
            success=False,
            metadata=metadata,
            human_takeover=bool(data.get("human_takeover")),
        )
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
        await self._apply_policy("ActivateWorkflowVersion", data)
        await ensure_approval(
            self.event_store,
            "ActivateWorkflowVersion",
            data,
            metadata=metadata,
        )
        if self.policy_engine and self.postgres:
            await self.policy_engine.validate_activation_metrics(
                self.postgres,
                "ActivateWorkflowVersion",
                data["workflow_id"],
            )
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
        await ensure_approval(
            self.event_store,
            "RollbackWorkflowVersion",
            data,
            metadata=metadata,
        )
        workflow = await self._load_workflow(data["workflow_id"])
        workflow.rollback_version(data.get("reason", ""))
        return await self._persist_workflow(
            workflow, command_id, correlation_id, metadata
        )

    async def _shadow_workflow_version(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        await self._apply_policy("ShadowWorkflowVersion", data)
        workflow = await self._load_workflow(data["workflow_id"])
        workflow.shadow_version(int(data.get("traffic_percent", 10)))
        result = await self._persist_workflow(
            workflow, command_id, correlation_id, metadata
        )
        if self.experiments:
            exp_id = await self.experiments.start_experiment(
                subject_type="workflow",
                subject_id=data["workflow_id"],
                version=workflow.version,
                mode="shadow",
                traffic_percent=int(data.get("traffic_percent", 10)),
            )
            result["experiment_id"] = exp_id
        return result

    async def _propose_change(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        change_id = data.get("change_id") or str(uuid4())
        event = ChangeProposed(
            change_id=change_id,
            change_type=data["change_type"],
            target_id=data["target_id"],
            hypothesis=data.get("hypothesis", ""),
            proposed_by=data["proposed_by"],
            payload=data.get("payload") or {},
        )
        records = await self._append_and_publish(
            "change",
            change_id,
            [event],
            command_id=command_id,
            correlation_id=correlation_id,
            metadata=metadata,
        )
        if self.postgres:
            try:
                await self.postgres.execute(
                    """
                    insert into change_proposals (
                      change_id, change_type, target_id, status, hypothesis,
                      proposed_by, payload, created_at, updated_at
                    )
                    values ($1, $2, $3, 'proposed', $4, $5, $6::jsonb, now(), now())
                    on conflict (change_id) do nothing
                    """,
                    change_id,
                    data["change_type"],
                    data["target_id"],
                    data.get("hypothesis", ""),
                    data["proposed_by"],
                    __import__("json").dumps(data.get("payload") or {}, default=str),
                )
            except Exception:
                pass
        return self._result(change_id, records)

    async def _propose_plugin(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        await self._apply_policy("ProposePlugin", data)
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
        await ensure_approval(
            self.event_store, "ActivatePlugin", data, metadata=metadata
        )
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
        await ensure_approval(
            self.event_store, "RollbackPlugin", data, metadata=metadata
        )
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
        action_type = approval.action_type
        target_id = approval.target_id
        approval.approve(data["approved_by"])
        result = await self._persist_approval(
            approval, command_id, correlation_id, metadata
        )
        if data.get("auto_execute", True):
            follow_up = await follow_up_after_grant(
                self,
                action_type=action_type,
                target_id=target_id,
                approval_id=str(approval.approval_id),
                approved_by=data["approved_by"],
                correlation_id=correlation_id,
                metadata=metadata,
            )
            if follow_up:
                result["follow_up"] = follow_up
        return result

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

    async def _apply_policy(self, command_type: str, data: dict[str, Any]) -> None:
        if self.policy_engine:
            self.policy_engine.validate_command(
                command_type, data, environment=self.environment
            )

    async def _register_resource(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        parsed = parse_uri(data["uri"])
        resource = Resource.register(
            uri=parsed.canonical,
            name=data["name"],
            adapter=parsed.adapter,
            classification=data.get("classification", "document"),
            metadata=data.get("metadata") or {},
            resource_id=data.get("resource_id"),
        )
        if self.transport:
            probe = await self.transport.probe(parsed.canonical)
            resource.metadata["probe"] = {
                "ok": probe.get("ok"),
                "size_bytes": probe.get("size_bytes"),
            }
        records = await self._append_and_publish(
            "resource",
            str(resource.resource_id),
            resource.get_uncommitted_events(),
            command_id=command_id,
            correlation_id=correlation_id,
            metadata=metadata,
        )
        resource.mark_events_committed()
        if self.rag_indexer:
            try:
                await self.rag_indexer.ingest_resource(
                    resource_id=str(resource.resource_id),
                    uri=resource.uri,
                    name=resource.name,
                    classification=resource.classification,
                )
            except Exception:
                pass
        return self._result(str(resource.resource_id), records)

    async def _request_transfer(
        self,
        command_id: str,
        data: dict[str, Any],
        correlation_id: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if not self.transport:
            raise ValueError("Transport service is not configured")

        resource_id = data["resource_id"]
        events = await self.event_store.get_events_for_aggregate("resource", resource_id)
        if not events:
            raise ValueError(f"Resource not found: {resource_id}")

        first = events[0].data
        source_uri = first["uri"]
        transfer_id = str(uuid4())
        resource = Resource(
            resource_id=ResourceId(resource_id),
            uri=source_uri,
            name=first.get("name", ""),
            adapter=first.get("adapter", "localfs"),
        )
        resource.request_transfer(
            transfer_id=transfer_id,
            destination_uri=data["destination_uri"],
            requested_by=data.get("requested_by", "system"),
        )
        pending = resource.get_uncommitted_events()
        records = await self._append_and_publish(
            "resource",
            resource_id,
            pending,
            command_id=command_id,
            correlation_id=correlation_id,
            metadata=metadata,
        )
        resource.mark_events_committed()

        outcome = await self.transport.copy(source_uri, data["destination_uri"])
        resource2 = Resource(
            resource_id=ResourceId(resource_id),
            uri=source_uri,
            name=first.get("name", ""),
            adapter=first.get("adapter", "localfs"),
        )
        if outcome.get("ok"):
            resource2.complete_transfer(transfer_id, outcome)
        else:
            resource2.fail_transfer(transfer_id, outcome.get("error") or "transfer failed")
        records2 = await self._append_and_publish(
            "resource",
            resource_id,
            resource2.get_uncommitted_events(),
            command_id=command_id,
            correlation_id=correlation_id,
            metadata=metadata,
        )
        return self._result(resource_id, [*records, *records2])

    async def _record_task_outcome(
        self,
        task: Task,
        *,
        success: bool,
        metadata: dict[str, Any] | None,
        human_takeover: bool = False,
    ) -> None:
        if not self.evaluation:
            return
        workflow_id = (task.metadata or {}).get("workflow_id")
        try:
            await self.evaluation.record_task_outcome(
                task_id=str(task.task_id),
                workflow_id=workflow_id,
                agent_id=str(task.agent_id) if task.agent_id else None,
                success=success,
                duration_ms=(task.metadata or {}).get("duration_ms"),
                human_takeover=human_takeover
                or (metadata or {}).get("actor", {}).get("type") == "human",
            )
            if (
                not success
                and workflow_id
                and self.evaluation
                and await self.evaluation.should_auto_rollback("workflow", workflow_id)
            ):
                await self.handle(
                    command_type="RollbackWorkflowVersion",
                    data={
                        "workflow_id": workflow_id,
                        "reason": "auto-rollback: metrics threshold breached",
                        "skip_approval": True,
                    },
                    metadata={"actor": {"type": "system", "id": "evaluation-engine"}},
                )
        except Exception:
            pass

    def _result(self, aggregate_id: str, records: list[Any]) -> dict[str, Any]:
        return {
            "aggregate_id": aggregate_id,
            "events": [
                record.to_message() if hasattr(record, "to_message") else record
                for record in records
            ],
        }
