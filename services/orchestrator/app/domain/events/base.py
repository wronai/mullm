from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, ClassVar
from uuid import uuid4


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _json_value(value: Any) -> Any:
    for value_type, converter in _JSON_VALUE_CONVERTERS:
        if isinstance(value, value_type):
            return converter(value)
    return getattr(value, "value", value)


def _json_datetime(value: datetime) -> str:
    return value.isoformat()


def _json_list(value: list[Any]) -> list[Any]:
    return [_json_value(item) for item in value]


def _json_dict(value: dict[Any, Any]) -> dict[Any, Any]:
    return {key: _json_value(item) for key, item in value.items()}


def _json_none(value: None) -> None:
    return None


_JSON_VALUE_CONVERTERS = (
    (datetime, _json_datetime),
    (list, _json_list),
    (dict, _json_dict),
    (type(None), _json_none),
)


@dataclass(frozen=True)
class DomainEvent:
    timestamp: datetime = field(default_factory=_utc_now)

    event_type: ClassVar[str]
    aggregate_type: ClassVar[str]

    @property
    def aggregate_id(self) -> str:
        raise NotImplementedError

    @property
    def data(self) -> dict[str, Any]:
        raise NotImplementedError

    def to_message(
        self,
        *,
        event_id: str | None = None,
        revision: int | None = None,
        causation_id: str | None = None,
        correlation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        aggregate_id = self.aggregate_id
        return {
            "event_id": event_id or str(uuid4()),
            "stream_id": f"{self.aggregate_type}-{aggregate_id}",
            "aggregate_type": self.aggregate_type,
            "aggregate_id": aggregate_id,
            "event_type": self.event_type,
            "revision": revision,
            "occurred_at": self.timestamp.isoformat(),
            "causation_id": causation_id,
            "correlation_id": correlation_id,
            "payload": self.data,
            "metadata": metadata or {},
        }
