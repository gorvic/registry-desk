"""Read-only model for imported registry snapshots."""

from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from registrydesk.domain.registry import RegistrySummary


class RegistryListModel(QAbstractTableModel):
    HEADERS = ("Дата довідки", "№ довідки", "Адреса", "Об’єктів", "Власників", "Імпортовано")

    def __init__(self, items: list[RegistrySummary] | None = None) -> None:
        super().__init__()
        self.items = list(items or [])

    def set_items(self, items: list[RegistrySummary]) -> None:
        self.beginResetModel()
        self.items = list(items)
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.items)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self.items):
            return None
        item = self.items[index.row()]
        if role == Qt.ItemDataRole.UserRole:
            return item.id
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        values = (
            item.formed_at,
            item.information_reference_number,
            item.query_address,
            item.property_count,
            item.owner_count,
            item.imported_at,
        )
        return values[index.column()]

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return section + 1

    def registry_at(self, row: int) -> RegistrySummary | None:
        return self.items[row] if 0 <= row < len(self.items) else None
