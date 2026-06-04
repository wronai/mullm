import pytest

from app.domain.aggregates.approval import Approval, ApprovalStatus


def test_approval_request_and_grant():
    approval = Approval.create_request(
        action_type="ActivatePlugin",
        target_id="plugin-shell",
        requested_by="user-admin",
    )
    approval.approve("user-ops")
    assert approval.status == ApprovalStatus.GRANTED
    assert len(approval.get_uncommitted_events()) == 2


def test_cannot_approve_twice():
    approval = Approval.create_request(
        action_type="Deploy",
        target_id="wf-1",
        requested_by="user-1",
    )
    approval.approve("user-2")
    with pytest.raises(ValueError):
        approval.approve("user-3")
