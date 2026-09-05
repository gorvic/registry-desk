"""Read-only model for imported registry snapshots."""

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from registrydesk.domain import RegistrySummary
from registrydesk.interfaces.gui.contracts import RegistryListColumn


class RegistryListModel(QAbstractTableModel):
    """Read-only Qt model for lightweight imported-registry summaries."""

    def __init__(self, items: list[RegistrySummary] | None = None) -> None:
        super().__init__()
        self._items = list(items or [])

    def set_items(self, items: list[RegistrySummary]) -> None:
        """Replace the snapshot list using one model reset notification."""
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        """Return top-level row count required by ``QAbstractTableModel``."""
        return 0 if parent.isValid() else len(self._items)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        """Return the fixed typed-column count for this table model."""
        return 0 if parent.isValid() else len(RegistryListColumn)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object | None:
        """Provide role-specific table values to Qt views."""
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        item = self._items[index.row()]
        if role == Qt.ItemDataRole.UserRole:
            return item.id
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        match RegistryListColumn(index.column()):
            case RegistryListColumn.FORMED_AT:
                return item.formed_at
            case RegistryListColumn.REFERENCE_NUMBER:
                return item.information_reference_number
            case RegistryListColumn.ADDRESS:
                return item.query_address
            case RegistryListColumn.PROPERTY_COUNT:
                return item.property_count
            case RegistryListColumn.OWNER_COUNT:
                return item.owner_count
            case RegistryListColumn.IMPORTED_AT:
                return item.imported_at

    def headerData(  # noqa: N802
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object | None:
        """Return typed horizontal labels and one-based vertical row labels."""
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return RegistryListColumn(section).label
        return section + 1

    def registry_at(self, row: int) -> RegistrySummary | None:
        """Return the domain summary behind a view row when it exists."""
        return self._items[row] if 0 <= row < len(self._items) else None
