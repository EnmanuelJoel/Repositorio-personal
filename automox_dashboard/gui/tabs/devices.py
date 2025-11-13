"""Devices tab showing device inventory."""
from __future__ import annotations

from typing import Iterable, List, Sequence
import pathlib

from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from ...models import Device
from ...utils import export_to_csv
from ..helpers import build_table_model


class DeviceFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.search_text = ""
        self.os_filter = "All"
        self.status_filter = "All"
        self.group_filter = "All"

    def filterAcceptsRow(self, source_row: int, parent) -> bool:
        model = self.sourceModel()
        name = model.index(source_row, 0, parent).data() or ""
        ip = model.index(source_row, 1, parent).data() or ""
        os_name = model.index(source_row, 2, parent).data() or ""
        status = model.index(source_row, 3, parent).data() or ""
        group = model.index(source_row, 5, parent).data() or ""
        needle = self.search_text.lower()
        if needle and needle not in name.lower() and needle not in ip.lower():
            return False
        if self.os_filter != "All" and os_name != self.os_filter:
            return False
        if self.group_filter != "All" and group != self.group_filter:
            return False
        if self.status_filter == "Online" and "Online" not in status:
            return False
        if self.status_filter == "Offline" and "Offline" not in status:
            return False
        if self.status_filter == "Needs reboot" and "reboot" not in status.lower():
            return False
        return True


class DevicesTab(QWidget):
    headers = ["Device", "IP", "OS", "Status", "Compliance", "Group"]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.devices: List[Device] = []
        self.table = QTableView(self)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.proxy = DeviceFilterProxy(self)
        self.table.setModel(self.proxy)
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText("Buscar dispositivo...")
        self.os_combo = QComboBox(self)
        self.status_combo = QComboBox(self)
        self.group_combo = QComboBox(self)
        self.export_button = QPushButton("Export CSV", self)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Buscar:"))
        filter_layout.addWidget(self.search_box)
        filter_layout.addWidget(QLabel("OS:"))
        filter_layout.addWidget(self.os_combo)
        filter_layout.addWidget(QLabel("Estado:"))
        filter_layout.addWidget(self.status_combo)
        filter_layout.addWidget(QLabel("Grupo:"))
        filter_layout.addWidget(self.group_combo)
        filter_layout.addStretch()
        filter_layout.addWidget(self.export_button)

        layout = QVBoxLayout(self)
        layout.addLayout(filter_layout)
        layout.addWidget(self.table)

        self.search_box.textChanged.connect(self._on_search)
        self.os_combo.currentTextChanged.connect(self._on_filters_changed)
        self.status_combo.currentTextChanged.connect(self._on_filters_changed)
        self.group_combo.currentTextChanged.connect(self._on_filters_changed)
        self.export_button.clicked.connect(self._export_csv)

        self.status_combo.addItems(["All", "Online", "Offline", "Needs reboot"])

    def update_data(self, devices: List[Device]) -> None:
        self.devices = devices
        rows = []
        for device in devices:
            status_text = "Online" if device.connected else "Offline"
            if device.needs_reboot:
                status_text += " (Needs reboot)"
            rows.append(
                (
                    device.name,
                    device.ip,
                    device.os_name,
                    status_text,
                    "Compliant" if device.compliant else "Needs patch",
                    device.group_name,
                )
            )
        model = build_table_model(self.headers, rows)
        self.proxy.setSourceModel(model)
        self.table.resizeColumnsToContents()
        os_values = sorted({device.os_name for device in devices if device.os_name})
        self.os_combo.blockSignals(True)
        self.os_combo.clear()
        self.os_combo.addItem("All")
        for name in os_values:
            self.os_combo.addItem(name)
        self.os_combo.blockSignals(False)
        groups = sorted({device.group_name for device in devices if device.group_name})
        self.group_combo.blockSignals(True)
        self.group_combo.clear()
        self.group_combo.addItem("All")
        for name in groups:
            self.group_combo.addItem(name)
        self.group_combo.blockSignals(False)

    def _on_search(self, text: str) -> None:
        self.proxy.search_text = text
        self.proxy.invalidateFilter()

    def _on_filters_changed(self) -> None:
        self.proxy.os_filter = self.os_combo.currentText()
        self.proxy.status_filter = self.status_combo.currentText()
        self.proxy.group_filter = self.group_combo.currentText()
        self.proxy.invalidateFilter()

    def _export_csv(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(self, "Export devices", "devices.csv", "CSV (*.csv)")
        if not file_path:
            return
        rows: Iterable[Sequence] = [device.as_row() for device in self.devices]
        export_to_csv(pathlib.Path(file_path), self.headers, rows)
