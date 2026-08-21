"""Main window and navigation."""

from __future__ import annotations

from pathlib import Path
import re

from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QStackedWidget

from registrydesk.application import RegistryApplication
from registrydesk.domain.export import DEFAULT_EXPORT_FIELDS
from registrydesk.interfaces.dialogs.export_dialog import ExportDialog
from registrydesk.interfaces.pages.registries_page import RegistriesPage
from registrydesk.interfaces.pages.registry_page import RegistryPage


_EXPORT_CONFIG = {
    "xlsx": ("Excel (*.xlsx)", ".xlsx"),
    "pdf": ("PDF (*.pdf)", ".pdf"),
    "csv": ("CSV (*.csv)", ".csv"),
}


class MainWindow(QMainWindow):
    def __init__(self, application: RegistryApplication) -> None:
        super().__init__()
        self._app = application
        self._last_export_fields = DEFAULT_EXPORT_FIELDS
        self._last_export_format = "xlsx"
        self.setWindowTitle("Registry Desk")
        self.resize(960, 760)

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self.registries_page = RegistriesPage()
        self.registry_page = RegistryPage()
        self._stack.addWidget(self.registries_page)
        self._stack.addWidget(self.registry_page)

        self.registries_page.add_requested.connect(self._import_pdf)
        self.registries_page.open_requested.connect(self._open_registry)
        self.registries_page.delete_requested.connect(self._delete_registry)
        self.registries_page.export_requested.connect(self._export_registry)
        self.registry_page.back_requested.connect(self._show_registries)
        self.registry_page.export_requested.connect(self._export_registry)

        self._show_registries()

    def _show_registries(self) -> None:
        try:
            registries = self._app.list_registries()
        except Exception as exc:
            self._error(str(exc))
            return
        self.registries_page.set_registries(registries)
        self._stack.setCurrentWidget(self.registries_page)

    def _open_registry(self, registry_id: int) -> None:
        try:
            registry = self._app.get_registry(registry_id)
        except Exception as exc:
            self._error(str(exc))
            return
        if registry is None:
            self._error("Реєстр не знайдено.")
            self._show_registries()
            return
        self.registry_page.set_registry(registry)
        self._stack.setCurrentWidget(self.registry_page)

    def _import_pdf(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Імпорт довідки ЦНАП",
            "",
            "PDF (*.pdf)",
        )
        if not filename:
            return
        try:
            registry_id = self._app.import_pdf(Path(filename))
            registry = self._app.get_registry(registry_id)
        except Exception as exc:
            self._error(str(exc))
            return
        self._show_registries()
        if registry is not None:
            QMessageBox.information(
                self,
                "Імпорт завершено",
                f"Імпортовано {len({row.property_id for row in registry.rows})} об’єктів "
                f"і {len(registry.rows)} записів власників.",
            )
            self._open_registry(registry_id)

    def _delete_registry(self, registry_id: int) -> None:
        registry = self._app.get_registry(registry_id)
        if registry is None:
            self._show_registries()
            return
        answer = QMessageBox.question(
            self,
            "Видалити реєстр",
            f"Видалити імпортовану довідку № {registry.information_reference_number or '—'}?\n\n"
            f"{registry.query_address}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self._app.delete_registry(registry_id)
        except Exception as exc:
            self._error(str(exc))
            return
        self._show_registries()

    def _export_registry(self, registry_id: int) -> None:
        registry = self._app.get_registry(registry_id)
        if registry is None:
            self._error("Реєстр не знайдено.")
            return

        dialog = ExportDialog(
            self,
            self._last_export_fields,
            self._last_export_format,
        )
        if dialog.exec() != ExportDialog.DialogCode.Accepted:
            return

        fields = dialog.selected_fields()
        export_format = dialog.selected_format()
        config = _EXPORT_CONFIG.get(export_format)
        if config is None:
            self._error(f"Непідтримуваний формат експорту: {export_format}")
            return

        self._last_export_fields = fields
        self._last_export_format = export_format
        file_filter, extension = config
        suggested = self._suggest_export_name(registry.query_address, extension)
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Експорт",
            suggested,
            file_filter,
        )
        if not filename:
            return

        path = Path(filename)
        if path.suffix.casefold() != extension:
            path = path.with_suffix(extension)

        try:
            self._app.export(registry_id, export_format, fields, path)
        except Exception as exc:
            self._error(str(exc))
            return
        QMessageBox.information(self, "Експорт завершено", f"Файл збережено:\n{path}")

    @staticmethod
    def _suggest_export_name(address: str, extension: str) -> str:
        text = address or "registry"
        text = re.sub(r"^(м\.?Київ|місто Київ),\s*", "", text, flags=re.I)
        text = text.replace("вулиця ", "").replace("будинок ", "")
        text = re.sub(r"[^0-9A-Za-zА-Яа-яІіЇїЄєҐґ._ -]+", "_", text)
        text = re.sub(r"\s+", "_", text).strip("_.")
        return f"{text or 'registry'}_власники{extension}"

    def _error(self, message: str) -> None:
        QMessageBox.critical(self, "RegistryDesk", message)
