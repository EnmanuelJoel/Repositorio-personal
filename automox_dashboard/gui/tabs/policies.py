"""Policies tab."""
from __future__ import annotations

from typing import Iterable, List, Sequence
import pathlib

from PySide6.QtCore import QSortFilterProxyModel
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableView, QVBoxLayout, QWidget

from ...models import Policy
from ...utils import export_to_csv
from ..helpers import build_table_model


class NameFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.text = ""

    def filterAcceptsRow(self, source_row: int, parent) -> bool:
        model = self.sourceModel()
        value = model.index(source_row, 1, parent).data() or ""
        if not self.text:
            return True
        return self.text.lower() in value.lower()


class PoliciesTab(QWidget):
    headers = ["Policy ID", "Name", "Type", "Status", "Groups"]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.policies: List[Policy] = []
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Buscar política...")
        self.table = QTableView(self)
        self.proxy = NameFilterProxy(self)
        self.table.setModel(self.proxy)
        self.export_button = QPushButton("Export CSV", self)

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

    def update_data(self, policies: List[Policy]) -> None:
        self.policies = policies
        rows = [policy.as_row() for policy in policies]
        model = build_table_model(self.headers, rows)
        self.proxy.setSourceModel(model)
        self.table.resizeColumnsToContents()

    def _on_search(self, text: str) -> None:
        self.proxy.text = text
        self.proxy.invalidateFilter()

    def _export_csv(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(self, "Export policies", "policies.csv", "CSV (*.csv)")
        if not file_path:
            return
        rows: Iterable[Sequence] = [policy.as_row() for policy in self.policies]
        export_to_csv(pathlib.Path(file_path), self.headers, rows)
