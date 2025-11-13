"""Helper functions for Qt models."""
from __future__ import annotations

from typing import Iterable, Sequence

from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel


def build_table_model(headers: Sequence[str], rows: Iterable[Sequence]) -> QStandardItemModel:
    model = QStandardItemModel()
    model.setColumnCount(len(headers))
    model.setHorizontalHeaderLabels(list(headers))
    for row in rows:
        items = []
        for value in row:
            item = QStandardItem(str(value))
            item.setEditable(False)
            items.append(item)
        model.appendRow(items)
    return model


def colorize_item(item: QStandardItem, *, foreground: QColor | None = None, background: QColor | None = None) -> None:
    if foreground:
        item.setData(foreground, Qt.ForegroundRole)
    if background:
        item.setData(background, Qt.BackgroundRole)
