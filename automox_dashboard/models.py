"""Data models used throughout the Automox dashboard."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Iterable, List, Sequence

from .utils import format_datetime_iso, parse_automox_datetime


@dataclass
class Device:
    id: int
    name: str
    ip: str
    os_name: str
    connected: bool
    compliant: bool
    group_id: int | None
    group_name: str = ""
    needs_reboot: bool = False
    issues: List[str] = field(default_factory=list)
    create_time: datetime | None = None
    pending_patches: int = 0
    oldest_pending_days: int = 0

    @classmethod
    def from_api(cls, payload: Dict) -> "Device":
        detail = payload.get("detail", {}) or {}
        compatibility = payload.get("compatibility_checks") or {}
        issues: List[str] = []
        if not payload.get("connected", False):
            issues.append("Offline")
        if payload.get("needs_reboot"):
            issues.append("Needs reboot")
        if any(compatibility.values()):
            issues.append("Compatibility issue")
        if payload.get("status", {}).get("device_status") == "not-ready":
            issues.append("Agent not ready")
        ip = ""
        addresses = detail.get("ip_addresses") or []
        if addresses:
            ip = addresses[0]
        elif payload.get("ip"):
            ip = payload["ip"]
        create_time = parse_automox_datetime(payload.get("create_time"))
        return cls(
            id=payload.get("id", 0),
            name=payload.get("display_name") or payload.get("hostname") or payload.get("name") or "",
            ip=ip,
            os_name=detail.get("os_name") or payload.get("os_family") or "",
            connected=bool(payload.get("connected", False)),
            compliant=bool(payload.get("compliant", False)),
            group_id=payload.get("server_group_id"),
            needs_reboot=bool(payload.get("needs_reboot")),
            issues=issues,
            create_time=create_time,
            pending_patches=payload.get("pending_count", 0),
            oldest_pending_days=payload.get("oldest_pending_days", 0),
        )

    def as_row(self) -> Sequence:
        return (
            self.name,
            self.ip,
            self.os_name,
            "Online" if self.connected else "Offline",
            "Compliant" if self.compliant else "Needs attention",
            self.group_name or "",
        )


@dataclass
class Policy:
    id: int
    name: str
    type_name: str
    status: str
    group_count: int

    @classmethod
    def from_api(cls, payload: Dict) -> "Policy":
        groups = payload.get("server_groups") or []
        return cls(
            id=payload.get("id", 0),
            name=payload.get("name") or "",
            type_name=payload.get("policy_type_name") or "",
            status=payload.get("status") or "",
            group_count=len(groups),
        )

    def as_row(self) -> Sequence:
        return (self.id, self.name, self.type_name, self.status, self.group_count)


@dataclass
class Group:
    id: int
    name: str
    device_count: int
    notes: str = ""
    policies_count: int = 0

    @classmethod
    def from_api(cls, payload: Dict) -> "Group":
        policies = payload.get("policies") or []
        name = payload.get("name") or "<Default Group>"
        return cls(
            id=payload.get("id", 0),
            name=name,
            device_count=payload.get("server_count", 0),
            notes=payload.get("notes") or "",
            policies_count=len(policies),
        )

    def as_row(self) -> Sequence:
        return (self.id, self.name, self.device_count, self.policies_count, self.notes)


@dataclass
class SoftwarePackage:
    device_id: int
    device_name: str
    name: str
    version: str
    installed: bool
    severity: str
    requires_reboot: bool
    create_time: datetime | None = None

    @classmethod
    def from_api(cls, payload: Dict, device_lookup: Dict[int, Device]) -> "SoftwarePackage":
        device_id = payload.get("server_id")
        device = device_lookup.get(device_id)
        create_time = parse_automox_datetime(payload.get("create_time"))
        return cls(
            device_id=device_id or 0,
            device_name=device.name if device else str(device_id or ""),
            name=payload.get("display_name") or payload.get("name") or "",
            version=payload.get("version") or "",
            installed=bool(payload.get("installed", False)),
            severity=_map_severity(payload.get("patch_classification_category_id")),
            requires_reboot=bool(payload.get("requires_reboot")),
            create_time=create_time,
        )

    def as_row(self) -> Sequence:
        return (
            self.device_name,
            self.name,
            self.version,
            "Installed" if self.installed else "Pending",
            self.severity,
            "Yes" if self.requires_reboot else "No",
        )


@dataclass
class ActivityEvent:
    timestamp: datetime | None
    event_type: str
    device_name: str
    policy_name: str
    description: str

    @classmethod
    def from_api(cls, payload: Dict) -> "ActivityEvent":
        timestamp = parse_automox_datetime(payload.get("event_time"))
        event_type = payload.get("event_name") or ""
        data = payload.get("data") or {}
        description = data.get("description") or payload.get("description") or ""
        return cls(
            timestamp=timestamp,
            event_type=event_type,
            device_name=payload.get("server_name") or data.get("server_name") or "",
            policy_name=data.get("policy_name") or payload.get("policy_name") or "",
            description=description,
        )

    def as_row(self) -> Sequence:
        return (
            format_datetime_iso(self.timestamp),
            self.event_type,
            self.device_name,
            self.policy_name,
            self.description,
        )


@dataclass
class PrePatchEntry:
    group_name: str
    device_name: str
    pending_total: int
    oldest_days: int
    critical_pending: int

    def as_row(self) -> Sequence:
        return (
            self.group_name,
            self.device_name,
            self.pending_total,
            self.critical_pending,
            self.oldest_days,
        )


def _map_severity(category_id: int | None) -> str:
    mapping = {
        3: "Critical",
        8: "Security",
        9: "Important",
    }
    return mapping.get(category_id, "Other")
