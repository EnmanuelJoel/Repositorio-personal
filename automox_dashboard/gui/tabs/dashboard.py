"""Dashboard tab implementation with KPIs and charts."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Dict

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QDateTimeAxis,
    QLineSeries,
    QPieSeries,
    QValueAxis,
)
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGridLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from ...data_manager import AppData


class DashboardTab(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.total_devices_label = QLabel("Total Devices: 0", self)
        self.compliant_label = QLabel("Compliant: 0%", self)
        self.trouble_label = QLabel("Devices with issues: 0", self)

        self.compliance_chart = QChartView(self)
        self.compliance_chart.setRenderHint(QPainter.Antialiasing)

        self.patch_line_chart = QChartView(self)
        self.patch_line_chart.setRenderHint(QPainter.Antialiasing)

        self.pending_bar_chart = QChartView(self)
        self.pending_bar_chart.setRenderHint(QPainter.Antialiasing)

        kpi_layout = QGridLayout()
        kpi_layout.addWidget(self.total_devices_label, 0, 0)
        kpi_layout.addWidget(self.compliant_label, 0, 1)
        kpi_layout.addWidget(self.trouble_label, 0, 2)

        layout = QVBoxLayout(self)
        layout.addLayout(kpi_layout)
        layout.addWidget(self.compliance_chart)
        layout.addWidget(self.patch_line_chart)
        layout.addWidget(self.pending_bar_chart)

    def update_data(self, data: AppData) -> None:
        devices = data.devices
        total = len(devices)
        compliant = sum(1 for device in devices if device.compliant)
        trouble = sum(1 for device in devices if device.issues)
        self.total_devices_label.setText(f"Total Devices: {total}")
        percent = 0 if total == 0 else (compliant / total) * 100
        self.compliant_label.setText(f"Compliant: {percent:.1f}%")
        self.trouble_label.setText(f"Devices with issues: {trouble}")
        self._update_compliance_chart(compliant, total - compliant)
        self._update_patch_line_chart(data)
        self._update_pending_bar_chart(data)

    def _update_compliance_chart(self, compliant: int, non_compliant: int) -> None:
        series = QPieSeries()
        series.append("Compliant", compliant)
        series.append("Needs Patch", non_compliant)
        series.setHoleSize(0.45)
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Compliance")
        chart.legend().setAlignment(Qt.AlignRight)
        self.compliance_chart.setChart(chart)

    def _update_patch_line_chart(self, data: AppData) -> None:
        points: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for event in data.events:
            if not event.timestamp:
                continue
            day = event.timestamp.strftime("%Y-%m-%d")
            if "patch.applied" in event.event_type:
                points["Applied"][day] += 1
            elif "patch.failed" in event.event_type:
                points["Failed"][day] += 1
        chart = QChart()
        chart.setTitle("Patch activity")
        if not points:
            axis_y = QValueAxis()
            axis_y.setRange(0, 1)
            chart.addAxis(axis_y, Qt.AlignLeft)
            self.patch_line_chart.setChart(chart)
            return
        min_day: datetime | None = None
        max_day: datetime | None = None
        for label, values in points.items():
            series = QLineSeries()
            series.setName(label)
            for day, count in sorted(values.items()):
                dt = datetime.strptime(day, "%Y-%m-%d")
                if min_day is None or dt < min_day:
                    min_day = dt
                if max_day is None or dt > max_day:
                    max_day = dt
                series.append(QPointF(dt.timestamp(), count))
            chart.addSeries(series)
        axis_x = QDateTimeAxis()
        axis_x.setFormat("dd MMM")
        axis_x.setTitleText("Date")
        axis_x.setTickCount(6)
        axis_y = QValueAxis()
        axis_y.setLabelFormat("%d")
        axis_y.setTitleText("Count")
        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)
        for series in chart.series():
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)
        self.patch_line_chart.setChart(chart)

    def _update_pending_bar_chart(self, data: AppData) -> None:
        ranges = ["0-30d", "31-60d", "61-90d", ">90d"]
        totals = {r: 0 for r in ranges}
        for entry in data.prepatch:
            if entry.oldest_days <= 30:
                totals["0-30d"] += entry.pending_total
            elif entry.oldest_days <= 60:
                totals["31-60d"] += entry.pending_total
            elif entry.oldest_days <= 90:
                totals["61-90d"] += entry.pending_total
            else:
                totals[">90d"] += entry.pending_total
        bar_set = QBarSet("Pending patches")
        for label in ranges:
            bar_set.append(totals[label])
        series = QBarSeries()
        series.append(bar_set)
        chart = QChart()
        chart.addSeries(series)
        axis_x = QBarCategoryAxis()
        axis_x.append(ranges)
        chart.addAxis(axis_x, Qt.AlignBottom)
        axis_y = QValueAxis()
        axis_y.setLabelFormat("%d")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)
        chart.setTitle("Outstanding patches by age")
        self.pending_bar_chart.setChart(chart)
