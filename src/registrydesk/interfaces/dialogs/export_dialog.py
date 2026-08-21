"""Technical export-field selection dialog."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from registrydesk.domain.export import (
    DEFAULT_EXPORT_FIELDS,
    EXPORT_FIELDS,
    EXPORT_FIELDS_BY_KEY,
    EXPORT_FORMATS,
)


class ExportDialog(QDialog):
    """Choose export format, fields, and their order using two simple lists."""

    def __init__(
        self,
        parent=None,
        selected: tuple[str, ...] = DEFAULT_EXPORT_FIELDS,
        export_format: str = "xlsx",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Експорт")
        self.resize(720, 500)

        self.format_combo = QComboBox()
        for key, label in EXPORT_FORMATS:
            self.format_combo.addItem(label, key)
        format_index = self.format_combo.findData(export_format)
        if format_index >= 0:
            self.format_combo.setCurrentIndex(format_index)

        self.available = QListWidget()
        self.selected = QListWidget()
        self.available.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.selected.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

        selected_set = set(selected)
        for field in EXPORT_FIELDS:
            if field.key not in selected_set:
                self.available.addItem(self._item(field.key, field.label))
        for key in selected:
            field = EXPORT_FIELDS_BY_KEY.get(key)
            if field is not None:
                self.selected.addItem(self._item(field.key, field.label))

        move_right = QPushButton("→")
        move_left = QPushButton("←")
        move_up = QPushButton("↑")
        move_down = QPushButton("↓")
        for button in (move_right, move_left, move_up, move_down):
            button.setFixedWidth(48)

        move_right.clicked.connect(self._move_right)
        move_left.clicked.connect(self._move_left)
        move_up.clicked.connect(self._move_up)
        move_down.clicked.connect(self._move_down)

        middle = QVBoxLayout()
        middle.addStretch(1)
        middle.addWidget(move_right)
        middle.addWidget(move_left)
        middle.addStretch(1)

        reorder = QVBoxLayout()
        reorder.addStretch(1)
        reorder.addWidget(move_up)
        reorder.addWidget(move_down)
        reorder.addStretch(1)

        left_box = QVBoxLayout()
        left_box.addWidget(QLabel("Доступні поля"))
        left_box.addWidget(self.available)

        right_box = QVBoxLayout()
        right_box.addWidget(QLabel("Поля для експорту"))
        right_box.addWidget(self.selected)

        lists = QHBoxLayout()
        lists.addLayout(left_box, 1)
        lists.addLayout(middle)
        lists.addLayout(right_box, 1)
        lists.addLayout(reorder)

        format_row = QHBoxLayout()
        format_row.addWidget(QLabel("Формат:"))
        format_row.addWidget(self.format_combo, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Експорт")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Скасувати")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(format_row)
        layout.addLayout(lists, 1)
        layout.addWidget(buttons)

    @staticmethod
    def _item(key: str, label: str) -> QListWidgetItem:
        item = QListWidgetItem(label)
        item.setData(Qt.ItemDataRole.UserRole, key)
        return item

    def selected_format(self) -> str:
        return str(self.format_combo.currentData())

    def selected_fields(self) -> tuple[str, ...]:
        return tuple(
            str(self.selected.item(row).data(Qt.ItemDataRole.UserRole))
            for row in range(self.selected.count())
        )

    def accept(self) -> None:
        if self.selected.count() == 0:
            return
        super().accept()

    def _move_right(self) -> None:
        row = self.available.currentRow()
        if row < 0:
            return
        self.selected.addItem(self.available.takeItem(row))
        self.selected.setCurrentRow(self.selected.count() - 1)

    def _move_left(self) -> None:
        row = self.selected.currentRow()
        if row < 0:
            return
        self.available.addItem(self.selected.takeItem(row))
        self.available.setCurrentRow(self.available.count() - 1)

    def _move_up(self) -> None:
        row = self.selected.currentRow()
        if row <= 0:
            return
        item = self.selected.takeItem(row)
        self.selected.insertItem(row - 1, item)
        self.selected.setCurrentRow(row - 1)

    def _move_down(self) -> None:
        row = self.selected.currentRow()
        if row < 0 or row >= self.selected.count() - 1:
            return
        item = self.selected.takeItem(row)
        self.selected.insertItem(row + 1, item)
        self.selected.setCurrentRow(row + 1)
