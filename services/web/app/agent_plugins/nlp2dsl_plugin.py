"""Plugin nlp2dsl — workflow / DSL (discuss); Mullm nie wykonuje DSL lokalnie."""

from __future__ import annotations

from app import nlp2dsl_bridge as nlp


class Nlp2DslPlugin:
    plugin_id = "nlp2dsl"
    title = "nlp2dsl (workflow DSL)"
    executor_agent_id = "coordinator"
    ingress_steps = frozenset({"nlp2dsl"})
    route_kinds = frozenset({"nlp2dsl", "workroom_hint"})

    async def health(self) -> bool:
        return await nlp.health()

    async def translate_shell(self, message: str, *, dsl: str = "shell") -> None:
        return None


plugin = Nlp2DslPlugin()
