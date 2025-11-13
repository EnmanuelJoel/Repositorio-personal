"""Pre-patch tab showing pending patch backlog."""
from __future__ import annotations

from typing import Iterable, List, Sequence
import pathlib

from PySide6.QtCore import QSortFilterProxyModel
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableView, QVBoxLayout, QWidget

from ...models import PrePatchEntry
from ...utils import export_to_csv
from ..helpers import build_table_model


class PrePatchFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.search = ""
        self.group_filter = "All"

    def filterAcceptsRow(self, source_row, parent) -> bool:
        model = self.sourceModel()
        group = model.index(source_row, 0, parent).data() or ""
        device = model.index(source_row, 1, parent).data() or ""
        if self.group_filter != "All" and group != self.group_filter:
            return False
        if not self.search:
            return True
        return self.search.lower() in device.lower()


class PrePatchTab(QWidget):
    headers = ["Group", "Device", "Pending", "Critical Pending", "Oldest patch (days)"]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.entries: List[PrePatchEntry] = []
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Buscar dispositivo...")
        self.export_button = QPushButton("Export CSV", self)
        self.table = QTableView(self)
        self.proxy = PrePatchFilterProxy(self)
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

    def update_data(self, entries: List[PrePatchEntry]) -> None:
        self.entries = entries
        rows = [entry.as_row() for entry in entries]
        model = build_table_model(self.headers, rows)
        self.proxy.setSourceModel(model)
        self.table.resizeColumnsToContents()

    def _on_search(self, text: str) -> None:
        self.proxy.search = text
        self.proxy.invalidateFilter()

    def _export_csv(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(self, "Export pre-patch", "prepatch.csv", "CSV (*.csv)")
        if not file_path:
            return
        rows: Iterable[Sequence] = [entry.as_row() for entry in self.entries]
        export_to_csv(pathlib.Path(file_path), self.headers, rows)
