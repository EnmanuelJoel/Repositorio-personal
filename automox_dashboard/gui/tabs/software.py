"""Software inventory tab."""
from __future__ import annotations

from typing import Iterable, List, Sequence
import pathlib

from PySide6.QtCore import QSortFilterProxyModel
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from ...models import SoftwarePackage
from ...utils import export_to_csv
from ..helpers import build_table_model


class SoftwareFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.search = ""
        self.device_filter = "All"
        self.pending_only = False

    def filterAcceptsRow(self, source_row, parent) -> bool:
        model = self.sourceModel()
        device = model.index(source_row, 0, parent).data() or ""
        name = model.index(source_row, 1, parent).data() or ""
        installed = model.index(source_row, 3, parent).data() or ""
        if self.search and self.search.lower() not in name.lower():
            return False
        if self.device_filter != "All" and device != self.device_filter:
            return False
        if self.pending_only and installed != "Pending":
            return False
        return True


class SoftwareTab(QWidget):
    headers = ["Device", "Software", "Version", "Status", "Severity", "Requires Reboot"]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.packages: List[SoftwarePackage] = []
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Buscar software...")
        self.device_combo = QComboBox(self)
        self.pending_check = QCheckBox("Solo pendientes", self)
        self.export_button = QPushButton("Export CSV", self)
        self.table = QTableView(self)
        self.proxy = SoftwareFilterProxy(self)
        self.table.setModel(self.proxy)

        filters = QHBoxLayout()
        filters.addWidget(QLabel("Software:"))
        filters.addWidget(self.search)
        filters.addWidget(QLabel("Dispositivo:"))
        filters.addWidget(self.device_combo)
        filters.addWidget(self.pending_check)
        filters.addStretch()
        filters.addWidget(self.export_button)

        layout = QVBoxLayout(self)
        layout.addLayout(filters)
        layout.addWidget(self.table)

        self.search.textChanged.connect(self._on_search)
        self.device_combo.currentTextChanged.connect(self._on_filters)
        self.pending_check.stateChanged.connect(self._on_filters)
        self.export_button.clicked.connect(self._export_csv)

    def update_data(self, packages: List[SoftwarePackage]) -> None:
        self.packages = packages
        rows = [pkg.as_row() for pkg in packages]
        model = build_table_model(self.headers, rows)
        self.proxy.setSourceModel(model)
        devices = sorted({pkg.device_name for pkg in packages})
        self.device_combo.blockSignals(True)
        self.device_combo.clear()
        self.device_combo.addItem("All")
        for name in devices:
            self.device_combo.addItem(name)
        self.device_combo.blockSignals(False)
        self.table.resizeColumnsToContents()

    def _on_search(self, text: str) -> None:
        self.proxy.search = text
        self.proxy.invalidateFilter()

    def _on_filters(self) -> None:
        self.proxy.device_filter = self.device_combo.currentText()
        self.proxy.pending_only = self.pending_check.isChecked()
        self.proxy.invalidateFilter()

    def _export_csv(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(self, "Export software", "software.csv", "CSV (*.csv)")
        if not file_path:
            return
        rows: Iterable[Sequence] = [pkg.as_row() for pkg in self.packages]
        export_to_csv(pathlib.Path(file_path), self.headers, rows)
