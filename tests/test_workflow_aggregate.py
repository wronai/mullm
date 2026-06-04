from app.domain.aggregates.workflow import Workflow
from app.domain.value_objects import WorkflowStatus


def test_start_workflow():
    workflow = Workflow.start(
        workflow_id="wf-deploy",
        input_data={"env": "staging"},
        agent_assignments={"step1": "shell-agent-a"},
    )
    assert workflow.status == WorkflowStatus.ACTIVE
    assert workflow.get_uncommitted_events()[0].event_type == "WorkflowStarted"


def test_version_lifecycle():
    workflow = Workflow.propose_version(
        workflow_id="wf-deploy",
        version=2,
        definition={"steps": ["lint", "test"]},
    )
    workflow.validate_version()
    workflow.approve_version("user-admin")
    workflow.activate_version()
    assert workflow.status == WorkflowStatus.ACTIVE
