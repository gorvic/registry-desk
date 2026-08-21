"""Read-only imported registry page with live search."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from registrydesk.domain.registry import RegistryDetails
from registrydesk.interfaces.models.registry_table_model import RegistryTableModel
from registrydesk.interfaces.models.search_proxy import AllColumnsSearchProxy


class RegistryPage(QWidget):
    back_requested = Signal()
    export_requested = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self._registry_id: int | None = None

        self.back_button = QPushButton("← Реєстри")
        self.title = QLabel()
        self.title.setStyleSheet("font-size: 16pt; font-weight: 600;")
        self.export_button = QPushButton("Експорт")

        header = QHBoxLayout()
        header.addWidget(self.back_button)
        header.addWidget(self.title, 1)
        header.addWidget(self.export_button)

        search_label = QLabel("Пошук:")
        self.search = QLineEdit()
        self.search.setPlaceholderText("№ квартири/приміщення, власник, реєстраційний номер, частка…")
        search_row = QHBoxLayout()
        search_row.addWidget(search_label)
        search_row.addWidget(self.search, 1)

        self.model = RegistryTableModel()
        self.proxy = AllColumnsSearchProxy()
        self.proxy.setSourceModel(self.model)
        self.proxy.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 320)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 140)
        self.table.setColumnWidth(5, 180)
        self.table.setColumnWidth(6, 190)

        self.status = QLabel()

        layout = QVBoxLayout(self)
        layout.addLayout(header)
        layout.addLayout(search_row)
        layout.addWidget(self.table)
        layout.addWidget(self.status)

        self.back_button.clicked.connect(self.back_requested.emit)
        self.export_button.clicked.connect(self._emit_export)
        self.search.textChanged.connect(self._search_changed)

    def set_registry(self, registry: RegistryDetails) -> None:
        self._registry_id = registry.id
        number = registry.information_reference_number or "—"
        self.title.setText(f"{registry.query_address} — довідка № {number}")
        self.model.set_rows(registry.rows)
        self.search.clear()
        self.status.setText(
            f"Записів власників: {len(registry.rows)} · Сторінок у довідці: {registry.page_count}"
        )

    def _search_changed(self, text: str) -> None:
        self.proxy.set_search_text(text)

    def _emit_export(self) -> None:
        if self._registry_id is not None:
            self.export_requested.emit(self._registry_id)
