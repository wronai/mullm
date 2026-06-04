from fastapi import APIRouter, HTTPException, Request
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


@router.post("")
async def post_command(command: CommandEnvelope, request: Request):
    """Submit a CQRS command envelope."""
    try:
        result = await request.app.state.command_bus.handle_envelope(command.model_dump())
        return {"accepted": True, "command_id": command.command_id, "result": result}
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
