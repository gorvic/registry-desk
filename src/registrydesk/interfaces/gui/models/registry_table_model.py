"""Read-only clean ownership table model."""

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from registrydesk.common import natural_text_key, property_unit_sort_key, ukrainian_text_key
from registrydesk.domain import PropertyType, RegistryRow
from registrydesk.interfaces.gui.contracts import RegistryTableColumn


class RegistryTableModel(QAbstractTableModel):
    """Read-only Qt model for normalized ownership rows with typed sorting."""

    def __init__(self, rows: tuple[RegistryRow, ...] = ()) -> None:
        super().__init__()
        self._rows = tuple(rows)

    def set_rows(self, rows: tuple[RegistryRow, ...]) -> None:
        """Replace all clean rows while preserving a simple immutable snapshot."""
        self.beginResetModel()
        self._rows = tuple(rows)
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        """Return top-level row count required by ``QAbstractTableModel``."""
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        """Return the fixed typed-column count for this table model."""
        return 0 if parent.isValid() else len(RegistryTableColumn)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object | None:
        """Provide role-specific table values to Qt views."""
        if not index.isValid() or not 0 <= index.row() < len(self._rows):
            return None
        if role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            return None
        return self._display_value(self._rows[index.row()], RegistryTableColumn(index.column()))

    def sort_key(
        self,
        row_index: int,
        column: int,
        *,
        descending: bool = False,
    ) -> tuple[object, ...]:
        """Return a typed stable sort key for the proxy model."""
        row = self._rows[row_index]
        column_key = RegistryTableColumn(column)
        property_key = property_unit_sort_key(
            row.property_type,
            row.unit_number,
            descending=descending if column_key is RegistryTableColumn.UNIT else False,
        )
        owner_key = ukrainian_text_key(row.owner_name)
        # Stable tie-breakers keep owner rows of one property together even
        # when the user sorts by a non-unit column.
        tie_breaker = (property_key, owner_key, row.property_id)

        match column_key:
            case RegistryTableColumn.UNIT:
                primary = property_key
            case RegistryTableColumn.OWNER:
                primary = owner_key
            case RegistryTableColumn.TOTAL_AREA:
                primary = row.total_area
            case RegistryTableColumn.SHARE:
                primary = row.share
            case RegistryTableColumn.OWNERSHIP_AREA:
                primary = row.ownership_area
            case RegistryTableColumn.REGISTRY_NUMBER:
                primary = natural_text_key(row.registry_number)
            case RegistryTableColumn.RIGHT_RECORD_NUMBERS:
                primary = tuple(natural_text_key(number) for number in row.right_record_numbers)
        return primary, tie_breaker

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
            return RegistryTableColumn(section).label
        return section + 1

    @staticmethod
    def _display_value(row: RegistryRow, column: RegistryTableColumn) -> object:
        match column:
            case RegistryTableColumn.UNIT:
                property_type = PropertyType.from_value(row.property_type)
                suffix = (
                    property_type.abbreviation
                    if property_type is not PropertyType.OTHER
                    else row.property_type
                )
                return f"{row.unit_number} {suffix}".strip()
            case RegistryTableColumn.OWNER:
                return row.owner_name
            case RegistryTableColumn.TOTAL_AREA:
                return str(row.total_area)
            case RegistryTableColumn.SHARE:
                return row.share_text
            case RegistryTableColumn.OWNERSHIP_AREA:
                return f"{row.ownership_area:.6f}".rstrip("0").rstrip(".")
            case RegistryTableColumn.REGISTRY_NUMBER:
                return row.registry_number
            case RegistryTableColumn.RIGHT_RECORD_NUMBERS:
                return ", ".join(row.right_record_numbers)
