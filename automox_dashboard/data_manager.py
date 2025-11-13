"""High level orchestration for fetching and transforming Automox data."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .api_client import AutomoxAPIClient
from .models import ActivityEvent, Device, Group, Policy, PrePatchEntry, SoftwarePackage
from .utils import DateRange


@dataclass
class AppData:
    devices: List[Device]
    policies: List[Policy]
    groups: List[Group]
    software: List[SoftwarePackage]
    events: List[ActivityEvent]
    prepatch: List[PrePatchEntry]


class DataManager:
    """Loads Automox data and builds domain models."""

    def __init__(self, base_url: str = "https://console.automox.com/api") -> None:
        self.base_url = base_url

    def load_all(self, api_key: str, org_id: int, date_range: DateRange) -> AppData:
        client = AutomoxAPIClient(api_key=api_key, org_id=org_id, base_url=self.base_url)
        devices_payload = client.get_devices()
        groups_payload = client.get_groups()
        policies_payload = client.get_policies()
        software_payload = client.get_software()
        events_payload = client.get_events(date_range.start_iso, date_range.end_iso)

        groups = [Group.from_api(row) for row in groups_payload]
        group_lookup = {group.id: group for group in groups}

        devices = [Device.from_api(row) for row in devices_payload]
        for device in devices:
            if device.group_id in group_lookup:
                device.group_name = group_lookup[device.group_id].name

        device_lookup = {device.id: device for device in devices}

        policies = [Policy.from_api(row) for row in policies_payload]
        software = [SoftwarePackage.from_api(row, device_lookup) for row in software_payload]
        events = [ActivityEvent.from_api(row) for row in events_payload]
        prepatch = self._build_prepatch(devices, software)
        return AppData(
            devices=devices,
            policies=policies,
            groups=groups,
            software=software,
            events=events,
            prepatch=prepatch,
        )

    def _build_prepatch(self, devices: List[Device], software: List[SoftwarePackage]) -> List[PrePatchEntry]:
        critical_map: Dict[int, int] = {}
        for pkg in software:
            if not pkg.installed and pkg.severity == "Critical":
                critical_map[pkg.device_id] = critical_map.get(pkg.device_id, 0) + 1
        entries: List[PrePatchEntry] = []
        for device in devices:
            if device.pending_patches <= 0:
                continue
            entries.append(
                PrePatchEntry(
                    group_name=device.group_name or "",
                    device_name=device.name,
                    pending_total=device.pending_patches,
                    critical_pending=critical_map.get(device.id, 0),
                    oldest_days=device.oldest_pending_days,
                )
            )
        return entries
