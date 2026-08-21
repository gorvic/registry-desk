"""Read-only clean ownership table model."""

from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from registrydesk.domain.registry import RegistryRow
from registrydesk.utils.sorting import (
    natural_text_key,
    property_unit_sort_key,
    ukrainian_text_key,
)


class RegistryTableModel(QAbstractTableModel):
    HEADERS = (
        "№",
        "Власник",
        "Загальна площа",
        "Частка",
        "Площа у власності",
        "Реєстраційний № об’єкта",
        "№ запису(ів) про право",
    )

    def __init__(self, rows: tuple[RegistryRow, ...] = ()) -> None:
        super().__init__()
        self.rows = tuple(rows)

    def set_rows(self, rows: tuple[RegistryRow, ...]) -> None:
        self.beginResetModel()
        self.rows = tuple(rows)
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self.rows):
            return None
        row = self.rows[index.row()]
        if role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            return None
        values = (
            self._unit_display(row),
            row.owner_name,
            str(row.total_area),
            row.share_text,
            f"{row.ownership_area:.6f}".rstrip("0").rstrip("."),
            row.registry_number,
            ", ".join(row.right_record_numbers),
        )
        return values[index.column()]

    def sort_key(self, row_index: int, column: int, *, descending: bool = False):
        """Return typed keys so GUI sorting follows human expectations."""
        row = self.rows[row_index]
        property_key = property_unit_sort_key(
            row.property_type,
            row.unit_number,
            descending=descending if column == 0 else False,
        )
        owner_key = ukrainian_text_key(row.owner_name)
        tie_breaker = (property_key, owner_key, row.property_id)

        primary = (
            property_key,
            owner_key,
            row.total_area,
            row.share,
            row.ownership_area,
            natural_text_key(row.registry_number),
            tuple(natural_text_key(number) for number in row.right_record_numbers),
        )[column]
        return primary, tie_breaker

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):  # noqa: N802
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return section + 1

    @staticmethod
    def _unit_display(row: RegistryRow) -> str:
        suffix = {
            "квартира": "кв.",
            "приміщення": "прим.",
        }.get(row.property_type, row.property_type)
        return f"{row.unit_number} {suffix}".strip()
