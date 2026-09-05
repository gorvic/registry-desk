"""Case-insensitive all-column search with model-provided typed sorting."""

from PySide6.QtCore import QModelIndex, QSortFilterProxyModel, Qt


class AllColumnsSearchProxy(QSortFilterProxyModel):
    """Case-insensitive all-column filtering with source-model sort semantics."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._needle = ""
        self._sort_order = Qt.SortOrder.AscendingOrder

    def set_search_text(self, text: str) -> None:
        """Normalize the search needle and invalidate the current filter."""
        self._needle = text.casefold().strip()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:  # noqa: N802
        """Accept a row when any visible source-model value contains the needle."""
        if not self._needle:
            return True
        model = self.sourceModel()
        if model is None:
            return True
        return any(
            (value := model.index(source_row, column, source_parent).data()) is not None
            and self._needle in str(value).casefold()
            for column in range(model.columnCount())
        )

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        """Remember direction because natural unit sorting depends on it."""
        self._sort_order = order
        super().sort(column, order)

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:  # noqa: N802
        """Compare rows through the source model's domain-aware sort key."""
        model = self.sourceModel()
        # Delegate domain-aware ordering to the source model instead of comparing
        # formatted display strings (for example ``10`` before ``2``).
        if model is not None and hasattr(model, "sort_key"):
            descending = self._sort_order == Qt.SortOrder.DescendingOrder
            return model.sort_key(
                left.row(), left.column(), descending=descending
            ) < model.sort_key(right.row(), right.column(), descending=descending)
        return super().lessThan(left, right)
