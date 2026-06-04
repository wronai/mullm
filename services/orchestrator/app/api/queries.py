from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uuid

router = APIRouter()


class TaskQuery(BaseModel):
    task_id: str


class AgentQuery(BaseModel):
    agent_id: str


class WorkflowQuery(BaseModel):
    workflow_id: str


class TaskListQuery(BaseModel):
    status: Optional[str] = None
    agent_id: Optional[str] = None
    limit: int = 50
    offset: int = 0


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    request: Request,
):
    """Get task by ID"""
    try:
        events = await request.app.state.event_store.get_events_for_aggregate("task", task_id)
        if not events:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Reconstruct task state from events
        task_state = {}
        for event in events:
            task_state.update(event.data)
        
        return {"task_id": task_id, "state": task_state, "events": [_event_to_dict(event) for event in events]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    request: Request,
):
    """Get agent by ID"""
    try:
        events = await request.app.state.event_store.get_events_for_aggregate("agent", agent_id)
        if not events:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Reconstruct agent state from events
        agent_state = {}
        for event in events:
            agent_state.update(event.data)
        
        return {"agent_id": agent_id, "state": agent_state, "events": [_event_to_dict(event) for event in events]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    request: Request,
):
    """Get workflow by ID"""
    try:
        events = await request.app.state.event_store.get_events_for_aggregate("workflow", workflow_id)
        if not events:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Reconstruct workflow state from events
        workflow_state = {}
        for event in events:
            workflow_state.update(event.data)
        
        return {"workflow_id": workflow_id, "state": workflow_state, "events": [_event_to_dict(event) for event in events]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def list_tasks(
    request: Request,
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List tasks with optional filtering"""
    try:
        event_store = request.app.state.event_store
        task_ids = await event_store.get_aggregate_ids("task")
        tasks = []

        for task_id in task_ids[offset : offset + limit]:
            events = await event_store.get_events_for_aggregate("task", task_id)
            item = _task_list_item(task_id, events, status=status, agent_id=agent_id)
            if item:
                tasks.append(item)

        return {"tasks": tasks, "total": len(task_ids)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _task_list_item(
    task_id: str,
    events: list[Any],
    *,
    status: str | None,
    agent_id: str | None,
) -> dict[str, Any] | None:
    if not events:
        return None
    task_state = _aggregate_state(events)
    if not _matches_task_filters(task_state, status=status, agent_id=agent_id):
        return None
    return {
        "task_id": task_id,
        "state": task_state,
        "last_updated": events[-1].timestamp,
    }


def _aggregate_state(events: list[Any]) -> dict[str, Any]:
    state: dict[str, Any] = {}
    for event in events:
        state.update(event.data)
    return state


def _matches_task_filters(
    task_state: dict[str, Any],
    *,
    status: str | None,
    agent_id: str | None,
) -> bool:
    if status and task_state.get("status") != status:
        return False
    if agent_id and task_state.get("agent_id") != agent_id:
        return False
    return True


@router.get("/agents")
async def list_agents(
    request: Request,
    limit: int = 50,
    offset: int = 0,
):
    """List all agents"""
    try:
        event_store = request.app.state.event_store
        agent_ids = await event_store.get_aggregate_ids("agent")
        agents = []
        
        for agent_id in agent_ids[offset:offset + limit]:
            events = await event_store.get_events_for_aggregate("agent", agent_id)
            if events:
                # Reconstruct agent state
                agent_state = {}
                for event in events:
                    agent_state.update(event.data)
                
                agents.append({
                    "agent_id": agent_id,
                    "state": agent_state,
                    "last_updated": events[-1].timestamp if events else None
                })
        
        return {"agents": agents, "total": len(agent_ids)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _event_to_dict(event):
    if hasattr(event, "to_message"):
        return event.to_message()
    return {
        "event_id": getattr(event, "event_id", None),
        "aggregate_type": getattr(event, "aggregate_type", None),
        "aggregate_id": getattr(event, "aggregate_id", None),
        "event_type": getattr(event, "event_type", None),
        "revision": getattr(event, "revision", None),
        "occurred_at": getattr(event, "timestamp", None),
        "payload": getattr(event, "data", {}),
        "metadata": getattr(event, "metadata", {}),
    }
