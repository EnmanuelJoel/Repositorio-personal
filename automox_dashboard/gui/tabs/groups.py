"""Groups tab."""
from __future__ import annotations

from typing import Iterable, List, Sequence
import pathlib

from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableView, QVBoxLayout, QWidget
from PySide6.QtCore import QSortFilterProxyModel

from ...models import Group
from ...utils import export_to_csv
from ..helpers import build_table_model


class GroupFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.text = ""

    def filterAcceptsRow(self, source_row, parent) -> bool:
        model = self.sourceModel()
        name = model.index(source_row, 1, parent).data() or ""
        if not self.text:
            return True
        return self.text.lower() in name.lower()


class GroupsTab(QWidget):
    headers = ["Group ID", "Name", "Devices", "Policies", "Notes"]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.groups: List[Group] = []
        self.search = QLineEdit(self)
        self.table = QTableView(self)
        self.proxy = GroupFilterProxy(self)
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

    def update_data(self, groups: List[Group]) -> None:
        self.groups = groups
        rows = [group.as_row() for group in groups]
        model = build_table_model(self.headers, rows)
        self.proxy.setSourceModel(model)
        self.table.resizeColumnsToContents()

    def _on_search(self, text: str) -> None:
        self.proxy.text = text
        self.proxy.invalidateFilter()

    def _export_csv(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(self, "Export groups", "groups.csv", "CSV (*.csv)")
        if not file_path:
            return
        rows: Iterable[Sequence] = [group.as_row() for group in self.groups]
        export_to_csv(pathlib.Path(file_path), self.headers, rows)
