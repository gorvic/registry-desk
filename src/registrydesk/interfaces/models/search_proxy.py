"""Case-insensitive all-column table search with human-friendly sorting."""

from __future__ import annotations

from PySide6.QtCore import QSortFilterProxyModel, Qt


class AllColumnsSearchProxy(QSortFilterProxyModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._needle = ""
        self._sort_order = Qt.SortOrder.AscendingOrder

    def set_search_text(self, text: str) -> None:
        self._needle = text.casefold().strip()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent) -> bool:  # noqa: N802
        if not self._needle:
            return True
        model = self.sourceModel()
        if model is None:
            return True
        for column in range(model.columnCount()):
            value = model.index(source_row, column, source_parent).data()
            if value is not None and self._needle in str(value).casefold():
                return True
        return False

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        self._sort_order = order
        super().sort(column, order)

    def lessThan(self, left, right) -> bool:  # noqa: N802
        """Use model-provided typed keys instead of lexicographic display strings."""
        model = self.sourceModel()
        if model is not None and hasattr(model, "sort_key"):
            descending = self._sort_order == Qt.SortOrder.DescendingOrder
            return model.sort_key(
                left.row(), left.column(), descending=descending
            ) < model.sort_key(
                right.row(), right.column(), descending=descending
            )
        return super().lessThan(left, right)
