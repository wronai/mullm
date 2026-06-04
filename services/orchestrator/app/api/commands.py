from fastapi import APIRouter, HTTPException, Request

from app.application.sagas.approval_gate import ApprovalRequired
from app.evolution.policy_engine import PolicyViolation
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import uuid

router = APIRouter()


class CommandEnvelope(BaseModel):
    command_id: Optional[str] = None
    aggregate_type: str
    aggregate_id: Optional[str] = None
    command_type: str
    occurred_at: Optional[str] = None
    actor: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    payload: Dict[str, Any]


class CreateTaskCommand(BaseModel):
    title: str
    description: Optional[str] = None
    agent_id: Optional[str] = None
    priority: str = "medium"
    execution_mode: str = "semi_auto"
    required_capabilities: list[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    auto_assign: bool = False
    shell_command: Optional[str] = None


class AssignTaskCommand(BaseModel):
    task_id: str
    agent_id: str
    command: Optional[str] = None


class StartTaskCommand(BaseModel):
    task_id: str


class CompleteTaskCommand(BaseModel):
    task_id: str
    result: Optional[Dict[str, Any]] = None


class FailTaskCommand(BaseModel):
    task_id: str
    error: str


class RegisterAgentCommand(BaseModel):
    agent_id: str
    agent_type: str
    capabilities: list[str]
    metadata: Optional[Dict[str, Any]] = None


class StartWorkflowCommand(BaseModel):
    workflow_id: str
    input_data: Dict[str, Any]
    agent_assignments: Optional[Dict[str, str]] = None


class ProposeWorkflowVersionCommand(BaseModel):
    workflow_id: str
    version: int
    definition: Dict[str, Any] = Field(default_factory=dict)


class WorkflowVersionCommand(BaseModel):
    workflow_id: str
    approval_id: Optional[str] = None
    skip_approval: bool = False
    approved_by: Optional[str] = None
    reason: Optional[str] = None


class ProposePluginCommand(BaseModel):
    plugin_id: str
    version: str
    capabilities: list[str] = Field(default_factory=list)
    manifest: Optional[Dict[str, Any]] = None


class PluginIdCommand(BaseModel):
    plugin_id: str
    approval_id: Optional[str] = None
    skip_approval: bool = False
    reason: Optional[str] = None


class CreateApprovalCommand(BaseModel):
    action_type: str
    target_id: str
    requested_by: str
    risk_level: str = "medium"
    approval_id: Optional[str] = None


class ApprovalActionCommand(BaseModel):
    approval_id: str
    approved_by: Optional[str] = None
    rejected_by: Optional[str] = None
    reason: Optional[str] = None
    auto_execute: bool = True


@router.post("")
async def post_command(command: CommandEnvelope, request: Request):
    """Submit a CQRS command envelope."""
    try:
        result = await request.app.state.command_bus.handle_envelope(command.model_dump())
        return {"accepted": True, "command_id": command.command_id, "result": result}
    except ApprovalRequired as e:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "approval_required",
                "message": str(e),
                "action_type": e.action_type,
                "target_id": e.target_id,
            },
        )
    except PolicyViolation as e:
        raise HTTPException(
            status_code=403,
            detail={"error": "policy_violation", "rule": e.rule, "message": str(e)},
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks")
async def create_task(
    command: CreateTaskCommand,
    request: Request,
):
    """Create a new task"""
    try:
        command_id = str(uuid.uuid4())
        result = await request.app.state.command_bus.handle(
            command_type="CreateTask",
            command_id=command_id,
            data=command.model_dump()
        )
        return {"command_id": command_id, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/assign")
async def assign_task(
    command: AssignTaskCommand,
    request: Request,
):
    """Assign a task to an agent"""
    try:
        command_id = str(uuid.uuid4())
        result = await request.app.state.command_bus.handle(
            command_type="AssignTask",
            command_id=command_id,
            data=command.model_dump()
        )
        return {"command_id": command_id, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/start")
async def start_task(
    command: StartTaskCommand,
    request: Request,
):
    """Mark a task as running."""
    try:
        command_id = str(uuid.uuid4())
        result = await request.app.state.command_bus.handle(
            command_type="StartTask",
            command_id=command_id,
            data=command.model_dump()
        )
        return {"command_id": command_id, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/complete")
async def complete_task(
    command: CompleteTaskCommand,
    request: Request,
):
    """Mark a task as completed"""
    try:
        command_id = str(uuid.uuid4())
        result = await request.app.state.command_bus.handle(
            command_type="CompleteTask",
            command_id=command_id,
            data=command.model_dump()
        )
        return {"command_id": command_id, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/fail")
async def fail_task(
    command: FailTaskCommand,
    request: Request,
):
    """Mark a task as failed."""
    try:
        command_id = str(uuid.uuid4())
        result = await request.app.state.command_bus.handle(
            command_type="FailTask",
            command_id=command_id,
            data=command.model_dump()
        )
        return {"command_id": command_id, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agents/register")
async def register_agent(
    command: RegisterAgentCommand,
    request: Request,
):
    """Register a new agent"""
    try:
        command_id = str(uuid.uuid4())
        result = await request.app.state.command_bus.handle(
            command_type="RegisterAgent",
            command_id=command_id,
            data=command.model_dump()
        )
        return {"command_id": command_id, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/workflows/start")
async def start_workflow(
    command: StartWorkflowCommand,
    request: Request,
):
    """Start a new workflow"""
    try:
        command_id = str(uuid.uuid4())
        result = await request.app.state.command_bus.handle(
            command_type="StartWorkflow",
            command_id=command_id,
            data=command.model_dump()
        )
        return {"command_id": command_id, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/workflows/versions/propose")
async def propose_workflow_version(command: ProposeWorkflowVersionCommand, request: Request):
    return await _dispatch(request, "ProposeWorkflowVersion", command.model_dump())


@router.post("/workflows/versions/validate")
async def validate_workflow_version(command: WorkflowVersionCommand, request: Request):
    return await _dispatch(request, "ValidateWorkflowVersion", command.model_dump())


@router.post("/workflows/versions/approve")
async def approve_workflow_version(command: WorkflowVersionCommand, request: Request):
    return await _dispatch(request, "ApproveWorkflowVersion", command.model_dump())


@router.post("/workflows/versions/activate")
async def activate_workflow_version(command: WorkflowVersionCommand, request: Request):
    return await _dispatch(request, "ActivateWorkflowVersion", command.model_dump())


@router.post("/workflows/versions/rollback")
async def rollback_workflow_version(command: WorkflowVersionCommand, request: Request):
    return await _dispatch(request, "RollbackWorkflowVersion", command.model_dump())


@router.post("/plugins/propose")
async def propose_plugin(command: ProposePluginCommand, request: Request):
    return await _dispatch(request, "ProposePlugin", command.model_dump())


@router.post("/plugins/validate")
async def validate_plugin(command: PluginIdCommand, request: Request):
    return await _dispatch(request, "ValidatePlugin", command.model_dump())


@router.post("/plugins/install")
async def install_plugin(command: PluginIdCommand, request: Request):
    return await _dispatch(request, "InstallPlugin", command.model_dump())


@router.post("/plugins/activate")
async def activate_plugin(command: PluginIdCommand, request: Request):
    return await _dispatch(request, "ActivatePlugin", command.model_dump())


@router.post("/plugins/rollback")
async def rollback_plugin(command: PluginIdCommand, request: Request):
    return await _dispatch(request, "RollbackPlugin", command.model_dump())


@router.post("/approvals/request")
async def create_approval(command: CreateApprovalCommand, request: Request):
    return await _dispatch(request, "CreateApprovalRequest", command.model_dump())


@router.post("/approvals/approve")
async def approve_request(command: ApprovalActionCommand, request: Request):
    return await _dispatch(
        request,
        "ApproveRequest",
        {
            "approval_id": command.approval_id,
            "approved_by": command.approved_by or "system",
            "auto_execute": command.auto_execute,
        },
    )


@router.post("/approvals/reject")
async def reject_request(command: ApprovalActionCommand, request: Request):
    return await _dispatch(
        request,
        "RejectRequest",
        {
            "approval_id": command.approval_id,
            "rejected_by": command.rejected_by or "system",
            "reason": command.reason or "",
        },
    )


@router.post("/approvals/expire")
async def expire_approval(command: ApprovalActionCommand, request: Request):
    return await _dispatch(
        request,
        "ExpireApproval",
        {"approval_id": command.approval_id},
    )


async def _dispatch(request: Request, command_type: str, data: dict) -> dict:
    try:
        command_id = str(uuid.uuid4())
        result = await request.app.state.command_bus.handle(
            command_type=command_type,
            command_id=command_id,
            data=data,
        )
        return {"command_id": command_id, "result": result}
    except ApprovalRequired as e:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "approval_required",
                "message": str(e),
                "action_type": e.action_type,
                "target_id": e.target_id,
            },
        )
    except PolicyViolation as e:
        raise HTTPException(
            status_code=403,
            detail={"error": "policy_violation", "rule": e.rule, "message": str(e)},
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
