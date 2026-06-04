# Domena Mullm

## Agregaty MVP

| Agregat | Granica |
|---------|---------|
| `Task` | Pojedyncza jednostka pracy |
| `Agent` | Capability i stan agenta |
| `Workflow` | Wersjonowana definicja procesu |
| `Plugin` | Lifecycle pluginu z manifestem |
| `Approval` | Bramka dla akcji ryzykownych |

## Komendy (write)

- Task: `CreateTask`, `AssignTask`, `StartTask`, `CompleteTask`, `FailTask`
- Agent: `RegisterAgent`, `AgentHeartbeat`
- Workflow: `StartWorkflow`, `ProposeWorkflowVersion`, `ValidateWorkflowVersion`, `ApproveWorkflowVersion`, `ActivateWorkflowVersion`, `RollbackWorkflowVersion`
- Plugin: `ProposePlugin`, `ValidatePlugin`, `InstallPlugin`, `ActivatePlugin`, `RollbackPlugin`
- Approval: `CreateApprovalRequest`, `ApproveRequest`, `RejectRequest`, `ExpireApproval`

## Read modele

- `operational_feed`, `task_board`, `agent_fleet`, `workflow_versions`
- `approval_requests`, `plugin_catalog`
