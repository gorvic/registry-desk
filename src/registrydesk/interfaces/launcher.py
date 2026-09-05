"""Qt launcher, single-instance guard and startup-only theme application."""

import ctypes
from pathlib import Path
import sys

from PySide6.QtCore import QSharedMemory
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from registrydesk.bootstrap import bootstrap
from registrydesk.config import AppSettings, RuntimePaths
from registrydesk.interfaces.gui.main_window import MainWindow
from registrydesk.interfaces.gui.theme import apply_theme

APP_NAME = "Registry Desk"
APP_USER_MODEL_ID = "RegistryDesk.RegistryDesk"
DEFAULT_SHARED_MEMORY_KEY = "registrydesk.application.single-instance"


class SingleInstanceGuard:
    """Process-local guard preventing two GUI instances from sharing one DB."""

    def __init__(self, key: str = DEFAULT_SHARED_MEMORY_KEY) -> None:
        self._memory = QSharedMemory(key)
        self._acquired = False

    def acquire(self) -> bool:
        """Acquire the shared-memory marker; return ``False`` if already owned."""
        if not self._acquired:
            self._acquired = self._memory.create(1)
        return self._acquired

    def release(self) -> None:
        """Detach the marker owned by this process, if any."""
        if self._acquired and self._memory.isAttached():
            self._memory.detach()
        self._acquired = False


def run() -> int:
    """Run at most one RegistryDesk GUI instance and return its exit code."""
    guard = SingleInstanceGuard()
    if not guard.acquire():
        return 0
    try:
        return _run_gui()
    finally:
        guard.release()


def _run_gui() -> int:
    """Create Qt, apply startup settings, compose the app and enter event loop."""
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)

    paths = RuntimePaths.discover()
    settings = AppSettings.load(paths.root)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setOrganizationName(APP_NAME)

    resources_dir = Path(__file__).resolve().parents[1] / "resources"
    icon_path = resources_dir / "RegistryDesk.ico"
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))
    apply_theme(app, settings.theme, resources_dir)

    result = bootstrap()
    window = MainWindow(result.app)
    window.show()
    return app.exec()
