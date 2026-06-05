# Response from Propact

**Status:** 200

## JSON Response

```json

{
  "route": "mullm_file_list",
  "handler": "conductor._mullm_file_list_turn",
  "intent": "file_list",
  "confidence": 0.92,
  "reason": "Lista plik\u00f3w (scope=user)",
  "reason_codes": [
    "intent_file_list",
    "scope_user"
  ],
  "requires_clarification": false,
  "fallback_route": "nlp2dsl",
  "candidate_routes": [
    {
      "route": "mullm_file_list",
      "handler": "conductor._mullm_file_list_turn",
      "intent": "file_list",
      "confidence": 0.92,
      "reason_codes": [
        "intent_file_list",
        "scope_user"
      ],
      "list_scope": "user"
    },
    {
      "route": "nlp2dsl",
      "handler": "nlp2dsl.workflow.chat",
      "intent": "workflow",
      "confidence": 0.35,
      "reason_codes": [
        "fallback_nlp2dsl"
      ]
    }
  ],
  "policy_flags": {
    "chat_mode": "discuss",
    "use_rag": false
  },
  "timing_ms": 0.04,
  "used_llm": false,
  "router_mode": "rules",
  "list_scope": "user"
}

```

## Raw Response

```

{"route":"mullm_file_list","handler":"conductor._mullm_file_list_turn","intent":"file_list","confidence":0.92,"reason":"Lista plików (scope=user)","reason_codes":["intent_file_list","scope_user"],"requires_clarification":false,"fallback_route":"nlp2dsl","candidate_routes":[{"route":"mullm_file_list","handler":"conductor._mullm_file_list_turn","intent":"file_list","confidence":0.92,"reason_codes":["intent_file_list","scope_user"],"list_scope":"user"},{"route":"nlp2dsl","handler":"nlp2dsl.workflow.chat","intent":"workflow","confidence":0.35,"reason_codes":["fallback_nlp2dsl"]}],"policy_flags":{"chat_mode":"discuss","use_rag":false},"timing_ms":0.04,"used_llm":false,"router_mode":"rules","list_scope":"user"}

```
