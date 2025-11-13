"""Activity log tab."""
from __future__ import annotations

from typing import Iterable, List, Sequence
import pathlib

from PySide6.QtCore import QSortFilterProxyModel
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QTableView, QVBoxLayout, QWidget

from ...models import ActivityEvent
from ...utils import export_to_csv
from ..helpers import build_table_model


class ActivityFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.search = ""
        self.event_filter = "All"

    def filterAcceptsRow(self, source_row, parent) -> bool:
        model = self.sourceModel()
        event = model.index(source_row, 1, parent).data() or ""
        device = model.index(source_row, 2, parent).data() or ""
        policy = model.index(source_row, 3, parent).data() or ""
        if self.event_filter != "All" and event != self.event_filter:
            return False
        if not self.search:
            return True
        needle = self.search.lower()
        return needle in device.lower() or needle in policy.lower()


class ActivityTab(QWidget):
    headers = ["Timestamp", "Event", "Device", "Policy", "Details"]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.events: List[ActivityEvent] = []
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Buscar por dispositivo o política...")
        self.event_combo = QComboBox(self)
        self.event_combo.addItems(["All", "system.patch.applied", "system.patch.failed", "system.policy.action"])
        self.export_button = QPushButton("Export CSV", self)
        self.table = QTableView(self)
        self.proxy = ActivityFilterProxy(self)
        self.table.setModel(self.proxy)

        filters = QHBoxLayout()
        filters.addWidget(QLabel("Evento:"))
        filters.addWidget(self.event_combo)
        filters.addWidget(QLabel("Buscar:"))
        filters.addWidget(self.search)
        filters.addStretch()
        filters.addWidget(self.export_button)

        layout = QVBoxLayout(self)
        layout.addLayout(filters)
        layout.addWidget(self.table)

        self.search.textChanged.connect(self._on_search)
        self.event_combo.currentTextChanged.connect(self._on_filters)
        self.export_button.clicked.connect(self._export_csv)

    def update_data(self, events: List[ActivityEvent]) -> None:
        self.events = events
        rows = [event.as_row() for event in events]
        model = build_table_model(self.headers, rows)
        self.proxy.setSourceModel(model)
        self.table.resizeColumnsToContents()

    def _on_search(self, text: str) -> None:
        self.proxy.search = text
        self.proxy.invalidateFilter()

    def _on_filters(self) -> None:
        self.proxy.event_filter = self.event_combo.currentText()
        self.proxy.invalidateFilter()

    def _export_csv(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(self, "Export events", "events.csv", "CSV (*.csv)")
        if not file_path:
            return
        rows: Iterable[Sequence] = [event.as_row() for event in self.events]
        export_to_csv(pathlib.Path(file_path), self.headers, rows)
