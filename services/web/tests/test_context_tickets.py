from app import workspace as ws


def test_unlink_ticket_removes_uri_and_linked_id():
    session = ws.new_session()
    tid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    ws.link_ticket(session.session_id, tid)
    assert f"mullm://ticket/{tid}" in session.context.uris
    assert session.context.linked_ticket_id == tid

    ctx = ws.unlink_ticket(session.session_id, tid)
    assert f"mullm://ticket/{tid}" not in ctx["uris"]
    assert ctx["linked_ticket_id"] is None


def test_unlink_ticket_keeps_other_uris():
    session = ws.new_session()
    tid = "11111111-2222-3333-4444-555555555555"
    ws.attach_context(session.session_id, uri="mullm://localfs/doc.txt")
    ws.link_ticket(session.session_id, tid)

    ctx = ws.unlink_ticket(session.session_id, tid)

    assert "mullm://localfs/doc.txt" in ctx["uris"]
    assert f"mullm://ticket/{tid}" not in ctx["uris"]


def test_clear_ticket_uris_removes_all_ticket_uris():
    session = ws.new_session()
    a = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    b = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    ws.link_ticket(session.session_id, a)
    ws.link_ticket(session.session_id, b)
    ws.attach_context(session.session_id, uri="mullm://localfs/x.txt")

    ctx = ws.clear_ticket_uris(session.session_id)

    assert ctx["uris"] == ["mullm://localfs/x.txt"]
    assert ctx["linked_ticket_id"] is None
