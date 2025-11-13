"""Utility helpers for the Automox desktop dashboard."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Sequence
import csv
import pathlib

ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass(frozen=True)
class DateRange:
    """Represents an inclusive UTC date range."""

    label: str
    start: datetime
    end: datetime

    @property
    def start_iso(self) -> str:
        return self.start.strftime(ISO_FORMAT)

    @property
    def end_iso(self) -> str:
        return self.end.strftime(ISO_FORMAT)


PREDEFINED_DATE_RANGES = {
    "Today": lambda now: DateRange(
        label="Today",
        start=datetime(now.year, now.month, now.day, tzinfo=timezone.utc),
        end=datetime(now.year, now.month, now.day, 23, 59, 59, tzinfo=timezone.utc),
    ),
    "Yesterday": lambda now: DateRange(
        label="Yesterday",
        start=datetime(now.year, now.month, now.day, tzinfo=timezone.utc) - timedelta(days=1),
        end=datetime(now.year, now.month, now.day, 23, 59, 59, tzinfo=timezone.utc) - timedelta(days=1),
    ),
    "Last 7 days": lambda now: DateRange(
        label="Last 7 days",
        start=now - timedelta(days=7),
        end=now,
    ),
    "Last 30 days": lambda now: DateRange(
        label="Last 30 days",
        start=now - timedelta(days=30),
        end=now,
    ),
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_automox_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.replace("+0000", "+00:00")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def format_datetime_iso(dt: datetime | None) -> str:
    if dt is None:
        return ""
    return dt.astimezone(timezone.utc).strftime(ISO_FORMAT)


def export_to_csv(path: pathlib.Path, headers: Sequence[str], rows: Iterable[Sequence[str | int | float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(["" if cell is None else cell for cell in row])
