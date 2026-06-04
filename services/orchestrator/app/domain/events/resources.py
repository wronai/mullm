from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from app.domain.events.base import DomainEvent
from app.domain.value_objects import ResourceId


@dataclass(frozen=True)
class CapabilityRegistered(DomainEvent):
    capability_id: str = ""
    source: str = "catalog"
    manifest: dict[str, Any] | None = None

    event_type: ClassVar[str] = "CapabilityRegistered"
    aggregate_type: ClassVar[str] = "capability"

    @property
    def aggregate_id(self) -> str:
        return self.capability_id

    @property
    def data(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "source": self.source,
            "manifest": self.manifest or {},
            "status": "active",
        }


@dataclass(frozen=True)
class ResourceRegistered(DomainEvent):
    resource_id: ResourceId = ResourceId("")
    uri: str = ""
    name: str = ""
    adapter: str = ""
    classification: str = "document"
    metadata: dict[str, Any] | None = None

    event_type: ClassVar[str] = "ResourceRegistered"
    aggregate_type: ClassVar[str] = "resource"

    @property
    def aggregate_id(self) -> str:
        return str(self.resource_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "resource_id": str(self.resource_id),
            "uri": self.uri,
            "name": self.name,
            "adapter": self.adapter,
            "classification": self.classification,
            "metadata": self.metadata or {},
            "status": "registered",
        }


@dataclass(frozen=True)
class TransferRequested(DomainEvent):
    resource_id: ResourceId = ResourceId("")
    transfer_id: str = ""
    source_uri: str = ""
    destination_uri: str = ""
    requested_by: str = ""

    event_type: ClassVar[str] = "TransferRequested"
    aggregate_type: ClassVar[str] = "resource"

    @property
    def aggregate_id(self) -> str:
        return str(self.resource_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "resource_id": str(self.resource_id),
            "transfer_id": self.transfer_id,
            "source_uri": self.source_uri,
            "destination_uri": self.destination_uri,
            "requested_by": self.requested_by,
            "status": "transferring",
        }


@dataclass(frozen=True)
class TransferCompleted(DomainEvent):
    resource_id: ResourceId = ResourceId("")
    transfer_id: str = ""
    outcome: dict[str, Any] | None = None

    event_type: ClassVar[str] = "TransferCompleted"
    aggregate_type: ClassVar[str] = "resource"

    @property
    def aggregate_id(self) -> str:
        return str(self.resource_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "resource_id": str(self.resource_id),
            "transfer_id": self.transfer_id,
            "outcome": self.outcome or {},
            "status": "available",
        }


@dataclass(frozen=True)
class TransferFailed(DomainEvent):
    resource_id: ResourceId = ResourceId("")
    transfer_id: str = ""
    error: str = ""

    event_type: ClassVar[str] = "TransferFailed"
    aggregate_type: ClassVar[str] = "resource"

    @property
    def aggregate_id(self) -> str:
        return str(self.resource_id)

    @property
    def data(self) -> dict[str, Any]:
        return {
            "resource_id": str(self.resource_id),
            "transfer_id": self.transfer_id,
            "error": self.error,
            "status": "error",
        }
