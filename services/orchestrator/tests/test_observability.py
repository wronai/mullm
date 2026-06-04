from app.observability.incidents import (
    IncidentCode,
    _event_payload,
    _incident_event_plan,
    classify_rag_failure,
)
from app.observability.export import format_logs_text


def test_classify_llm_unavailable():
    code = classify_rag_failure(llm_error="openrouter: not a valid model id")
    assert code == IncidentCode.LLM_UNAVAILABLE


def test_classify_empty_sources():
    code = classify_rag_failure(source_count=0)
    assert code == IncidentCode.RETRIEVER_EMPTY_RESULT


def test_classify_grounding():
    code = classify_rag_failure(llm_error="rate limit", source_count=3)
    assert code == IncidentCode.GROUNDING_FAILED


def test_classify_backend_500():
    code = classify_rag_failure(http_status=500)
    assert code == IncidentCode.RAG_BACKEND_UNAVAILABLE


def test_format_logs_text_keeps_observability_sections():
    text = format_logs_text(
        {
            "generated_at": "2026-06-04T00:00:00+00:00",
            "correlation_id": "corr-1",
            "rag_health": {
                "status": "degraded",
                "primary_incident_code": "RAG_BACKEND_UNAVAILABLE",
                "checks": [{"name": "retriever", "status": "ok", "detail": "ready"}],
                "recommendations": ["restart backend"],
            },
            "incidents": [
                {
                    "created_at": "2026-06-04T00:00:00+00:00",
                    "incident_code": "RAG_BACKEND_UNAVAILABLE",
                    "severity": "high",
                    "message": "backend down",
                    "retrieval_trace_id": "trace-1",
                }
            ],
            "incident_feed": [
                {
                    "created_at": "2026-06-04T00:00:00+00:00",
                    "incident_code": "RAG_BACKEND_UNAVAILABLE",
                    "status": "open",
                    "message": "backend down",
                }
            ],
            "rag_snapshots": [{"created_at": "2026-06-04T00:00:00+00:00", "status": "ok"}],
            "session": {
                "session_id": "sess-1",
                "context": {"ticket_id": "ABC-1"},
                "events": [{"type": "RagIncident", "summary": "incident"}],
                "chat_history": [{"role": "user", "content": "co jest w pliku"}],
            },
        }
    )

    assert "## RAG health" in text
    assert "## Incidents" in text
    assert "trace=trace-1" in text
    assert "## Workspace session" in text
    assert "## Raw JSON" in text


def test_incident_event_plan_includes_diagnostics_and_remediation():
    row = {
        "incident_id": "inc-1",
        "component": "rag",
        "incident_code": IncidentCode.RAG_BACKEND_UNAVAILABLE.value,
        "diagnostics": {"checks": [{"name": "retriever", "status": "ok"}]},
        "remediation": {
            "attempted": True,
            "status": "succeeded",
            "verification": {"ok": True},
        },
    }

    events = [event_type for event_type, _ in _incident_event_plan(row)]

    assert events == [
        "RagRequestFailed",
        "IncidentDetected",
        "IncidentClassified",
        "DiagnosticsStarted",
        "DiagnosticsCompleted",
        "RemediationStarted",
        "RemediationSucceeded",
        "PostRemediationVerificationPassed",
    ]


def test_event_payload_adds_diagnostics_details():
    payload = _event_payload(
        "DiagnosticsCompleted",
        {
            "incident_id": "inc-1",
            "incident_code": IncidentCode.RAG_BACKEND_UNAVAILABLE.value,
            "correlation_id": "corr-1",
            "component": "rag",
            "message": "backend down",
            "diagnostics": {
                "checks": [{"name": "retriever", "status": "ok"}],
                "root_cause": "backend",
            },
        },
    )

    assert payload["status"] == "diagnosed"
    assert payload["checks"]["retriever"]["status"] == "ok"
    assert payload["root_cause"] == "backend"
