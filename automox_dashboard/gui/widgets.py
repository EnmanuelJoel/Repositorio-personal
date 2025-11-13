"""Reusable Qt widgets for the Automox dashboard."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Sequence
import pathlib

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from ..utils import export_to_csv


@dataclass
class TableConfig:
    headers: Sequence[str]
    export_headers: Sequence[str] | None = None


class FilterableTable(QWidget):
    """Simple widget bundling a search bar, table view and export button."""

    def __init__(self, *, title: str, model, parent=None) -> None:
        super().__init__(parent)
        self.model = model
        self.table = QTableView(self)
        self.table.setModel(model)
        self.table.setSortingEnabled(True)
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText(f"Buscar en {title}...")
        self.export_button = QPushButton("Export CSV", self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.search_box)
        layout.addWidget(self.table)
        layout.addWidget(self.export_button)

    def connect_export(self, headers: Sequence[str], rows_provider: Callable[[], Iterable[Sequence]]):
        def handle_export() -> None:
            file_path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
            if not file_path:
                return
            export_to_csv(pathlib.Path(file_path), headers, rows_provider())

        self.export_button.clicked.connect(handle_export)

