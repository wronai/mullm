from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from app.domain.events import (
    ResourceRegistered,
    TransferCompleted,
    TransferFailed,
    TransferRequested,
)
from app.domain.value_objects import ResourceId


@dataclass
class Resource:
    resource_id: ResourceId
    uri: str
    name: str
    adapter: str
    classification: str = "document"
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "registered"
    _events: list[Any] = field(default_factory=list)

    @classmethod
    def register(
        cls,
        *,
        uri: str,
        name: str,
        adapter: str,
        classification: str = "document",
        metadata: dict[str, Any] | None = None,
        resource_id: str | None = None,
    ) -> "Resource":
        resource = cls(
            resource_id=ResourceId(resource_id or str(uuid4())),
            uri=uri,
            name=name,
            adapter=adapter,
            classification=classification,
            metadata=metadata or {},
        )
        resource._events.append(
            ResourceRegistered(
                resource_id=resource.resource_id,
                uri=uri,
                name=name,
                adapter=adapter,
                classification=classification,
                metadata=resource.metadata,
            )
        )
        return resource

    def request_transfer(
        self,
        *,
        transfer_id: str,
        destination_uri: str,
        requested_by: str,
    ) -> None:
        self.status = "transferring"
        self._events.append(
            TransferRequested(
                resource_id=self.resource_id,
                transfer_id=transfer_id,
                source_uri=self.uri,
                destination_uri=destination_uri,
                requested_by=requested_by,
            )
        )

    def complete_transfer(self, transfer_id: str, outcome: dict[str, Any]) -> None:
        self.status = "available"
        self._events.append(
            TransferCompleted(
                resource_id=self.resource_id,
                transfer_id=transfer_id,
                outcome=outcome,
            )
        )

    def fail_transfer(self, transfer_id: str, error: str) -> None:
        self.status = "error"
        self._events.append(
            TransferFailed(
                resource_id=self.resource_id,
                transfer_id=transfer_id,
                error=error,
            )
        )

    def get_uncommitted_events(self) -> list[Any]:
        return self._events.copy()

    def mark_events_committed(self) -> None:
        self._events.clear()
