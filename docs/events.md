# Eventy Mullm

## Envelope komendy

```json
{
  "command_id": "cmd-…",
  "aggregate_type": "Task",
  "aggregate_id": "task-123",
  "command_type": "CreateTask",
  "actor": {"type": "user", "id": "user-admin"},
  "payload": {"title": "Sprawdź pipeline", "priority": "high"}
}
```

## Envelope eventu

```json
{
  "event_id": "evt-…",
  "stream_id": "task-task-123",
  "aggregate_type": "task",
  "aggregate_id": "task-123",
  "event_type": "TaskCreated",
  "revision": 1,
  "occurred_at": "2026-06-04T15:30:01Z",
  "causation_id": "cmd-…",
  "payload": {"title": "…", "status": "pending"}
}
```

## Kluczowe eventy

- Task: `TaskCreated`, `TaskAssigned`, `TaskStarted`, `TaskCompleted`, `TaskFailed`
- Agent: `AgentRegistered`, `TaskAssignedToAgent`, `AgentMarkedIdle`
- Workflow: `WorkflowVersionProposed` … `WorkflowVersionActivated`
- Plugin: `PluginProposed` … `PluginActivated`
- Approval: `ApprovalRequested`, `ApprovalGranted`, `ApprovalRejected`
