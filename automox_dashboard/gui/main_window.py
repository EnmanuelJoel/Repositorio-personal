"""Main window and application wiring."""
from __future__ import annotations

from datetime import datetime, timezone

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QIntValidator, QKeySequence, QAction
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..api_client import AutomoxAPIError, AutomoxRateLimitError
from ..data_manager import AppData, DataManager
from ..utils import DateRange, PREDEFINED_DATE_RANGES, utc_now
from .tabs.activity import ActivityTab
from .tabs.dashboard import DashboardTab
from .tabs.devices import DevicesTab
from .tabs.groups import GroupsTab
from .tabs.policies import PoliciesTab
from .tabs.prepatch import PrePatchTab
from .tabs.software import SoftwareTab
from .tabs.troubleshooting import TroubleshootingTab


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Automox Dashboard")
        self.resize(1200, 800)
        self.data_manager = DataManager()
        self.app_data: AppData | None = None

        self.api_key_edit = QLineEdit(self)
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.org_id_edit = QLineEdit(self)
        self.org_id_edit.setValidator(QIntValidator(1, 999999999, self))
        self.date_combo = QComboBox(self)
        self.date_combo.addItems(list(PREDEFINED_DATE_RANGES.keys()) + ["Custom"])
        self.start_date = QDateEdit(self)
        self.end_date = QDateEdit(self)
        for widget in (self.start_date, self.end_date):
            widget.setDisplayFormat("yyyy-MM-dd")
            widget.setCalendarPopup(True)
            widget.hide()
        self.load_button = QPushButton("Cargar datos", self)
        self.load_button.clicked.connect(self.load_data)
        self.date_combo.currentTextChanged.connect(self._toggle_custom_dates)

        form = QHBoxLayout()
        form.addWidget(QLabel("API Key:"))
        form.addWidget(self.api_key_edit)
        form.addWidget(QLabel("Org ID:"))
        form.addWidget(self.org_id_edit)
        form.addWidget(QLabel("Rango:"))
        form.addWidget(self.date_combo)
        form.addWidget(self.start_date)
        form.addWidget(self.end_date)
        form.addWidget(self.load_button)

        self.dashboard_tab = DashboardTab(self)
        self.devices_tab = DevicesTab(self)
        self.policies_tab = PoliciesTab(self)
        self.groups_tab = GroupsTab(self)
        self.software_tab = SoftwareTab(self)
        self.activity_tab = ActivityTab(self)
        self.prepatch_tab = PrePatchTab(self)
        self.troubleshooting_tab = TroubleshootingTab(self)

        self.tabs = QTabWidget(self)
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.devices_tab, "Devices")
        self.tabs.addTab(self.policies_tab, "Policies")
        self.tabs.addTab(self.groups_tab, "Groups")
        self.tabs.addTab(self.software_tab, "Software")
        self.tabs.addTab(self.activity_tab, "Activity Log")
        self.tabs.addTab(self.prepatch_tab, "Pre-Patch")
        self.tabs.addTab(self.troubleshooting_tab, "Troubleshooting")

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.addLayout(form)
        layout.addWidget(self.tabs)
        self.setCentralWidget(central)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self._setup_shortcuts()

    def _setup_shortcuts(self) -> None:
        reload_action = QAction("Reload", self)
        reload_action.setShortcut(QKeySequence("Ctrl+R"))
        reload_action.triggered.connect(self.load_data)
        self.addAction(reload_action)

        export_action = QAction("Export", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self._trigger_export)
        self.addAction(export_action)

        find_action = QAction("Find", self)
        find_action.setShortcut(QKeySequence("Ctrl+F"))
        find_action.triggered.connect(self._focus_search)
        self.addAction(find_action)

    def _toggle_custom_dates(self, text: str) -> None:
        is_custom = text == "Custom"
        for widget in (self.start_date, self.end_date):
            widget.setVisible(is_custom)
        if is_custom:
            today = QDate.currentDate()
            self.start_date.setDate(today)
            self.end_date.setDate(today)

    def _current_range(self) -> DateRange:
        selection = self.date_combo.currentText()
        if selection == "Custom":
            start = datetime(
                self.start_date.date().year(),
                self.start_date.date().month(),
                self.start_date.date().day(),
                tzinfo=timezone.utc,
            )
            end = datetime(
                self.end_date.date().year(),
                self.end_date.date().month(),
                self.end_date.date().day(),
                23,
                59,
                59,
                tzinfo=timezone.utc,
            )
            return DateRange(label="Custom", start=start, end=end)
        now = utc_now()
        factory = PREDEFINED_DATE_RANGES.get(selection)
        if factory:
            return factory(now)
        return PREDEFINED_DATE_RANGES["Last 7 days"](now)

    def load_data(self) -> None:
        api_key = self.api_key_edit.text().strip()
        org_text = self.org_id_edit.text().strip()
        if not api_key or not org_text:
            QMessageBox.warning(self, "Datos incompletos", "Debe ingresar API Key y Org ID")
            return
        self.load_button.setEnabled(False)
        self._set_status("Cargando datos...", error=False)
        try:
            org_id = int(org_text)
            date_range = self._current_range()
            data = self.data_manager.load_all(api_key, org_id, date_range)
        except AutomoxRateLimitError as exc:
            self._set_status(str(exc), error=True)
        except AutomoxAPIError as exc:
            self._set_status(str(exc), error=True)
        except Exception as exc:  # pragma: no cover - unexpected
            self._set_status(f"Error inesperado: {exc}", error=True)
        else:
            self.app_data = data
            self._update_tabs(data)
            self._set_status("Datos cargados correctamente", error=False)
        finally:
            self.load_button.setEnabled(True)

    def _update_tabs(self, data: AppData) -> None:
        self.dashboard_tab.update_data(data)
        self.devices_tab.update_data(data.devices)
        self.policies_tab.update_data(data.policies)
        self.groups_tab.update_data(data.groups)
        self.software_tab.update_data(data.software)
        self.activity_tab.update_data(data.events)
        self.prepatch_tab.update_data(data.prepatch)
        self.troubleshooting_tab.update_data(data.devices)

    def _set_status(self, message: str, *, error: bool) -> None:
        palette = "color: #ffffff; background-color: #c62828" if error else "color: #0f5132; background-color: #d1e7dd"
        self.status_bar.setStyleSheet(palette)
        self.status_bar.showMessage(message, 5000)

    def _focus_search(self) -> None:
        widget = self.tabs.currentWidget()
        search_widget = getattr(widget, "search", None) or getattr(widget, "search_box", None)
        if search_widget:
            search_widget.setFocus(Qt.ShortcutFocusReason)

    def _trigger_export(self) -> None:
        widget = self.tabs.currentWidget()
        button = getattr(widget, "export_button", None)
        if button:
            button.click()
