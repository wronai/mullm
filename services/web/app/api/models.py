from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ChatSessionStart(BaseModel):
    ticket_id: str = ""
    project: str = ""


class ChatMessage(BaseModel):
    session_id: str | None = None
    message: str = ""
    mode: str = "discuss"  # discuss | create_task | run_task | search_context
    use_rag: bool = True
    form_values: dict[str, Any] | None = None
    wait_for_confirmation: bool = False


class TaskDraftRequest(BaseModel):
    session_id: str
    message: str


class CreateTaskBody(BaseModel):
    session_id: str | None = None
    title: str
    description: str = ""
    shell_command: str | None = None
    auto_assign: bool = True
    wait_for_confirmation: bool = False
    priority: str = "medium"
    ticket_id: str | None = None


class CreateFromDraftBody(BaseModel):
    session_id: str
    draft: dict[str, Any] | None = None
    run: bool = False
    wait_for_confirmation: bool = False


class ConfirmTicketBody(BaseModel):
    session_id: str = ""


class SessionRef(BaseModel):
    session_id: str


class ContextAttachBody(BaseModel):
    session_id: str
    ticket_id: str | None = None
    project: str | None = None
    branch: str | None = None
    agent_id: str | None = None
    resource_id: str | None = None
    uri: str | None = None
    note: str | None = None
    filename: str | None = None


class WorkroomStart(BaseModel):
    user_session_id: str | None = None


class WorkroomMessage(BaseModel):
    message: str
    wait_for_confirmation: bool = False


class RoutingFeedbackBody(BaseModel):
    session_id: str
    turn_id: str
    rating: str  # good | partial | bad
    expected_route: str | None = None
    expected_reply_hint: str = ""
    improvement_notes: str = ""
    tags: list[str] | None = None
    user_message: str | None = None


class AccessMatrixBody(BaseModel):
    resources: list[dict[str, Any]] | None = None
    agents: list[dict[str, Any]] | None = None
    humans: list[dict[str, Any]] | None = None
    agent_resource: dict[str, dict[str, bool]] | None = None
    human_agent: dict[str, dict[str, bool]] | None = None
    default_all: bool | None = None
