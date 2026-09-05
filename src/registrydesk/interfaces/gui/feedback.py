"""Centralized user feedback dialogs."""

from PySide6.QtWidgets import QMessageBox, QWidget


class GuiFeedback:
    """Centralize message-box wording and confirmation semantics."""

    @staticmethod
    def error(parent: QWidget, message: str) -> None:
        """Show an operation failure using the application error title."""
        QMessageBox.critical(parent, "RegistryDesk", message)

    @staticmethod
    def info(parent: QWidget, title: str, message: str) -> None:
        """Show non-error completion information."""
        QMessageBox.information(parent, title, message)

    @staticmethod
    def confirm_delete(parent: QWidget, reference: str, address: str) -> bool:
        """Ask for explicit confirmation before destructive registry deletion."""
        answer = QMessageBox.question(
            parent,
            "Видалити реєстр",
            f"Видалити імпортовану довідку № {reference or '—'}?\n\n{address}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes
