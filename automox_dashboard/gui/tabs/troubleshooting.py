"""Troubleshooting tab listing problematic devices."""
from __future__ import annotations

from typing import Iterable, List, Sequence
import pathlib

from PySide6.QtCore import QSortFilterProxyModel
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableView, QVBoxLayout, QWidget

from ...models import Device
from ...utils import export_to_csv
from ..helpers import build_table_model


class TroubleshootingProxy(QSortFilterProxyModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.search = ""

    def filterAcceptsRow(self, source_row, parent) -> bool:
        model = self.sourceModel()
        device = model.index(source_row, 0, parent).data() or ""
        if not self.search:
            return True
        return self.search.lower() in device.lower()


class TroubleshootingTab(QWidget):
    headers = ["Device", "Group", "Issues", "Last seen"]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.devices: List[Device] = []
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Buscar dispositivo...")
        self.export_button = QPushButton("Export CSV", self)
        self.table = QTableView(self)
        self.proxy = TroubleshootingProxy(self)
        self.table.setModel(self.proxy)

        top = QHBoxLayout()
        top.addWidget(QLabel("Buscar:"))
        top.addWidget(self.search)
        top.addStretch()
        top.addWidget(self.export_button)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.table)

        self.search.textChanged.connect(self._on_search)
        self.export_button.clicked.connect(self._export_csv)

    def update_data(self, devices: List[Device]) -> None:
        trouble = [device for device in devices if device.issues]
        self.devices = trouble
        rows = []
        for device in trouble:
            issues = ", ".join(device.issues)
            rows.append((device.name, device.group_name, issues, ""))
        model = build_table_model(self.headers, rows)
        self.proxy.setSourceModel(model)
        self.table.resizeColumnsToContents()

    def _on_search(self, text: str) -> None:
        self.proxy.search = text
        self.proxy.invalidateFilter()

    def _export_csv(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(self, "Export troubleshooting", "troubleshooting.csv", "CSV (*.csv)")
        if not file_path:
            return
        rows: Iterable[Sequence] = [
            (device.name, device.group_name, ", ".join(device.issues), "")
            for device in self.devices
        ]
        export_to_csv(pathlib.Path(file_path), self.headers, rows)
