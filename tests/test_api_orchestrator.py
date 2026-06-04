def test_health_not_on_minimal_app(api_client):
    """Minimal test app exposes command routes only."""
    response = api_client.post(
        "/api/commands/tasks",
        json={"title": "API task", "priority": "high"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "command_id" in body
    assert body["result"]["aggregate_id"]


def test_register_agent_api(api_client):
    response = api_client.post(
        "/api/commands/agents/register",
        json={
            "agent_id": "shell-agent-a",
            "agent_type": "shell",
            "capabilities": ["shell"],
        },
    )
    assert response.status_code == 200


def test_approval_api_flow(api_client):
    created = api_client.post(
        "/api/commands/approvals/request",
        json={
            "action_type": "ActivatePlugin",
            "target_id": "plugin-x",
            "requested_by": "user-1",
        },
    )
    assert created.status_code == 200
    approval_id = created.json()["result"]["aggregate_id"]

    approved = api_client.post(
        "/api/commands/approvals/approve",
        json={
            "approval_id": approval_id,
            "approved_by": "user-ops",
            "auto_execute": False,
        },
    )
    assert approved.status_code == 200


def test_plugin_api_flow(api_client):
    proposed = api_client.post(
        "/api/commands/plugins/propose",
        json={
            "plugin_id": "deploy-tools",
            "version": "1.0.0",
            "capabilities": ["shell"],
            "manifest": {
                "risk_level": "low",
                "inputs": {},
                "outputs": {},
                "health_check": "/health",
                "rollback_strategy": "disable",
            },
        },
    )
    assert proposed.status_code == 200
    plugin_id = proposed.json()["result"]["aggregate_id"]

    for path in (
        "/api/commands/plugins/validate",
        "/api/commands/plugins/install",
    ):
        response = api_client.post(path, json={"plugin_id": plugin_id})
        assert response.status_code == 200, (path, response.text)

    blocked = api_client.post(
        "/api/commands/plugins/activate",
        json={"plugin_id": plugin_id},
    )
    assert blocked.status_code == 403
    assert blocked.json()["detail"]["error"] == "approval_required"

    approval = api_client.post(
        "/api/commands/approvals/request",
        json={
            "action_type": "ActivatePlugin",
            "target_id": plugin_id,
            "requested_by": "admin",
        },
    )
    approval_id = approval.json()["result"]["aggregate_id"]
    activated = api_client.post(
        "/api/commands/approvals/approve",
        json={"approval_id": approval_id, "approved_by": "ops"},
    )
    assert activated.status_code == 200
    assert "follow_up" in activated.json()["result"]


def test_workflow_version_api(api_client):
    proposed = api_client.post(
        "/api/commands/workflows/versions/propose",
        json={
            "workflow_id": "wf-ci",
            "version": 1,
            "definition": {"steps": ["lint"]},
        },
    )
    assert proposed.status_code == 200
    workflow_id = proposed.json()["result"]["aggregate_id"]

    for path in (
        "/api/commands/workflows/versions/validate",
        "/api/commands/workflows/versions/approve",
    ):
        response = api_client.post(
            path,
            json={"workflow_id": workflow_id, "approved_by": "admin"},
        )
        assert response.status_code == 200, (path, response.text)

    wf_approval = api_client.post(
        "/api/commands/approvals/request",
        json={
            "action_type": "ActivateWorkflowVersion",
            "target_id": workflow_id,
            "requested_by": "admin",
        },
    )
    approval_id = wf_approval.json()["result"]["aggregate_id"]
    activated = api_client.post(
        "/api/commands/approvals/approve",
        json={
            "approval_id": approval_id,
            "approved_by": "ops",
            "auto_execute": False,
        },
    )
    assert activated.status_code == 200


def test_command_envelope(api_client):
    response = api_client.post(
        "/api/commands",
        json={
            "aggregate_type": "Task",
            "aggregate_id": "ignored",
            "command_type": "CreateTask",
            "payload": {"title": "Envelope task"},
        },
    )
    assert response.status_code == 200
    assert response.json()["accepted"] is True
