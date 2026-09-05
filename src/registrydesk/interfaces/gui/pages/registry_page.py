"""Read-only imported registry page with live search."""

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

from registrydesk.domain import RegistryDetails
from registrydesk.interfaces.gui.geometry import REGISTRY_TABLE_COLUMN_WIDTHS
from registrydesk.interfaces.gui.models.registry_table_model import RegistryTableModel
from registrydesk.interfaces.gui.models.search_proxy import AllColumnsSearchProxy


class RegistryPage(QWidget):
    """Passive read-only detail page with local filtering and sorting."""

    back_requested = Signal()
    export_requested = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self._registry_id: int | None = None

        self.back_button = QPushButton("← Реєстри")
        self.title = QLabel()
        self.title.setProperty("registryTitle", True)
        self.export_button = QPushButton("Експорт")

        header = QHBoxLayout()
        header.addWidget(self.back_button)
        header.addWidget(self.title, 1)
        header.addWidget(self.export_button)

        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "№ квартири/приміщення, власник, реєстраційний номер, частка…"
        )
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Пошук:"))
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
        for column, width in REGISTRY_TABLE_COLUMN_WIDTHS.items():
            self.table.setColumnWidth(column.value, width)

        self.status = QLabel()

        layout = QVBoxLayout(self)
        layout.addLayout(header)
        layout.addLayout(search_row)
        layout.addWidget(self.table)
        layout.addWidget(self.status)

        self.back_button.clicked.connect(self.back_requested.emit)
        self.export_button.clicked.connect(self._emit_export)
        self.search.textChanged.connect(self.proxy.set_search_text)

    def set_registry(self, registry: RegistryDetails) -> None:
        """Display a complete registry read model and reset local search state."""
        self._registry_id = registry.id
        number = registry.information_reference_number or "—"
        self.title.setText(f"{registry.query_address} — довідка № {number}")
        self.model.set_rows(registry.rows)
        self.search.clear()
        self.status.setText(
            f"Записів власників: {len(registry.rows)} · Сторінок у довідці: {registry.page_count}"
        )

    def _emit_export(self) -> None:
        if self._registry_id is not None:
            self.export_requested.emit(self._registry_id)
