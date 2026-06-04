from app.observability.incidents import IncidentCode, classify_rag_failure


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
