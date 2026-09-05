"""GUI orchestration for registry navigation and operations."""

from PySide6.QtWidgets import QDialog, QStackedWidget, QWidget

from registrydesk.application import RegistryApplication
from registrydesk.domain import DEFAULT_EXPORT_FIELDS, ErrorMessage, ExportFormat
from registrydesk.interfaces.gui.dialogs.export_dialog import ExportDialog
from registrydesk.interfaces.gui.feedback import GuiFeedback
from registrydesk.interfaces.gui.files import (
    choose_export_path,
    choose_import_pdf,
    suggest_export_name,
)
from registrydesk.interfaces.gui.pages.registries_page import RegistriesPage
from registrydesk.interfaces.gui.pages.registry_page import RegistryPage


class RegistryController:
    """Own GUI navigation and user-triggered registry workflows.

    The controller is the only GUI object that coordinates dialogs, feedback
    and ``RegistryApplication`` calls.  Pages remain passive views and the
    application facade remains unaware of Qt.
    """

    def __init__(
        self,
        application: RegistryApplication,
        parent: QWidget,
        stack: QStackedWidget,
        registries_page: RegistriesPage,
        registry_page: RegistryPage,
    ) -> None:
        self._app = application
        self._parent = parent
        self._stack = stack
        self.registries_page = registries_page
        self.registry_page = registry_page
        self._last_export_fields = DEFAULT_EXPORT_FIELDS
        self._last_export_format = ExportFormat.XLSX

    def show_registries(self) -> None:
        """Refresh and display the imported-registry list page."""
        # Qt event handlers are the outermost operation boundary: exceptions
        # must become user feedback instead of escaping into the event loop.
        try:
            registries = self._app.list_registries()
        except Exception as exc:
            GuiFeedback.error(self._parent, str(exc))
            return
        self.registries_page.set_registries(registries)
        self._stack.setCurrentWidget(self.registries_page)

    def open_registry(self, registry_id: int) -> None:
        """Load one registry read model and navigate to its detail page."""
        try:
            registry = self._app.get_registry(registry_id)
        except Exception as exc:
            GuiFeedback.error(self._parent, str(exc))
            return
        if registry is None:
            GuiFeedback.error(self._parent, ErrorMessage.REGISTRY_NOT_FOUND)
            self.show_registries()
            return
        self.registry_page.set_registry(registry)
        self._stack.setCurrentWidget(self.registry_page)

    def import_pdf(self) -> None:
        """Run the interactive PDF import flow from file picker to detail page."""
        path = choose_import_pdf(self._parent)
        if path is None:
            return
        try:
            registry_id = self._app.import_pdf(path)
            registry = self._app.get_registry(registry_id)
        except Exception as exc:
            GuiFeedback.error(self._parent, str(exc))
            return

        self.show_registries()
        if registry is None:
            return
        GuiFeedback.info(
            self._parent,
            "Імпорт завершено",
            f"Імпортовано {len({row.property_id for row in registry.rows})} об’єктів "
            f"і {len(registry.rows)} записів власників.",
        )
        self.open_registry(registry_id)

    def delete_registry(self, registry_id: int) -> None:
        """Confirm and delete one persisted registry snapshot."""
        try:
            registry = self._app.get_registry(registry_id)
        except Exception as exc:
            GuiFeedback.error(self._parent, str(exc))
            return
        if registry is None:
            self.show_registries()
            return
        if not GuiFeedback.confirm_delete(
            self._parent,
            registry.information_reference_number,
            registry.query_address,
        ):
            return
        try:
            self._app.delete_registry(registry_id)
        except Exception as exc:
            GuiFeedback.error(self._parent, str(exc))
            return
        self.show_registries()

    def export_registry(self, registry_id: int) -> None:
        """Run field/format selection and export for one registry."""
        try:
            registry = self._app.get_registry(registry_id)
        except Exception as exc:
            GuiFeedback.error(self._parent, str(exc))
            return
        if registry is None:
            GuiFeedback.error(self._parent, ErrorMessage.REGISTRY_NOT_FOUND)
            return

        dialog = ExportDialog(
            self._parent,
            self._last_export_fields,
            self._last_export_format,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        fields = dialog.selected_fields()
        export_format = dialog.selected_format()
        suggested = suggest_export_name(registry.query_address, export_format)
        path = choose_export_path(self._parent, export_format, suggested)
        if path is None:
            return

        self._last_export_fields = fields
        self._last_export_format = export_format
        try:
            self._app.export(registry_id, export_format, fields, path)
        except Exception as exc:
            GuiFeedback.error(self._parent, str(exc))
            return
        GuiFeedback.info(self._parent, "Експорт завершено", f"Файл збережено:\n{path}")
