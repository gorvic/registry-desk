"""Start page with imported registry snapshots."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from registrydesk.domain import RegistrySummary
from registrydesk.interfaces.gui.geometry import REGISTRY_LIST_COLUMN_WIDTHS
from registrydesk.interfaces.gui.models.registry_list_model import RegistryListModel


class RegistriesPage(QWidget):
    """Passive start page listing imported registry snapshots."""

    add_requested = Signal()
    open_requested = Signal(int)
    delete_requested = Signal(int)
    export_requested = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        title = QLabel("Імпортовані реєстри")
        title.setProperty("pageTitle", True)

        self.add_button = QPushButton("Додати")
        self.open_button = QPushButton("Відкрити")
        self.export_button = QPushButton("Експорт")
        self.delete_button = QPushButton("Видалити")

        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch(1)
        for button in (
            self.add_button,
            self.open_button,
            self.export_button,
            self.delete_button,
        ):
            header.addWidget(button)

        self.model = RegistryListModel()
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        for column, width in REGISTRY_LIST_COLUMN_WIDTHS.items():
            self.table.setColumnWidth(column.value, width)

        layout = QVBoxLayout(self)
        layout.addLayout(header)
        layout.addWidget(self.table)

        self.add_button.clicked.connect(self.add_requested.emit)
        self.open_button.clicked.connect(self._emit_open)
        self.export_button.clicked.connect(self._emit_export)
        self.delete_button.clicked.connect(self._emit_delete)
        self.table.doubleClicked.connect(lambda _index: self._emit_open())
        self.table.selectionModel().selectionChanged.connect(lambda *_: self._sync_buttons())
        self._sync_buttons()

    def set_registries(self, registries: list[RegistrySummary]) -> None:
        """Replace visible registry summaries and synchronize action states."""
        self.model.set_items(registries)
        self._sync_buttons()

    def selected_registry(self) -> RegistrySummary | None:
        """Return the currently selected summary, if any."""
        indexes = self.table.selectionModel().selectedRows()
        return self.model.registry_at(indexes[0].row()) if indexes else None

    def _sync_buttons(self) -> None:
        enabled = self.selected_registry() is not None
        self.open_button.setEnabled(enabled)
        self.export_button.setEnabled(enabled)
        self.delete_button.setEnabled(enabled)

    def _emit_open(self) -> None:
        registry = self.selected_registry()
        if registry is not None:
            self.open_requested.emit(registry.id)

    def _emit_export(self) -> None:
        registry = self.selected_registry()
        if registry is not None:
            self.export_requested.emit(registry.id)

    def _emit_delete(self) -> None:
        registry = self.selected_registry()
        if registry is not None:
            self.delete_requested.emit(registry.id)
