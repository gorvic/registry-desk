"""Main GUI shell and signal wiring."""

from PySide6.QtWidgets import QMainWindow, QStackedWidget

from registrydesk.application import RegistryApplication
from registrydesk.interfaces.gui.controllers.registry import RegistryController
from registrydesk.interfaces.gui.geometry import MAIN_WINDOW_MINIMUM_SIZE, MAIN_WINDOW_SIZE
from registrydesk.interfaces.gui.pages.registries_page import RegistriesPage
from registrydesk.interfaces.gui.pages.registry_page import RegistryPage


class MainWindow(QMainWindow):
    """Top-level Qt shell that owns pages and signal wiring only.

    Registry operations live in ``RegistryController``; keeping the window
    focused on composition makes page behavior easy to reason about and test.
    """

    def __init__(self, application: RegistryApplication) -> None:
        super().__init__()
        self.setWindowTitle("Registry Desk")
        self.resize(*MAIN_WINDOW_SIZE)
        self.setMinimumSize(*MAIN_WINDOW_MINIMUM_SIZE)

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)
        self.registries_page = RegistriesPage()
        self.registry_page = RegistryPage()
        self._stack.addWidget(self.registries_page)
        self._stack.addWidget(self.registry_page)

        self._controller = RegistryController(
            application,
            self,
            self._stack,
            self.registries_page,
            self.registry_page,
        )
        self._connect_signals()
        self._controller.show_registries()

    def _connect_signals(self) -> None:
        """Wire passive page signals to the single registry controller."""
        self.registries_page.add_requested.connect(self._controller.import_pdf)
        self.registries_page.open_requested.connect(self._controller.open_registry)
        self.registries_page.delete_requested.connect(self._controller.delete_registry)
        self.registries_page.export_requested.connect(self._controller.export_registry)
        self.registry_page.back_requested.connect(self._controller.show_registries)
        self.registry_page.export_requested.connect(self._controller.export_registry)
