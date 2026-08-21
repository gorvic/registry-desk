"""Qt application entry point."""

from __future__ import annotations

import ctypes
from pathlib import Path
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from registrydesk.bootstrap import bootstrap
from registrydesk.interfaces.main_window import MainWindow


APP_NAME = "Registry Desk"
APP_USER_MODEL_ID = "RegistryDesk.RegistryDesk"


def run() -> int:
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            APP_USER_MODEL_ID
        )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setOrganizationName(APP_NAME)

    resources_dir = Path(__file__).resolve().parent / "resources"

    icon_path = resources_dir / "RegistryDesk.ico"
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))

    qss_path = resources_dir / "app.qss"
    if qss_path.is_file():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    result = bootstrap()

    window = MainWindow(result.app)
    window.show()
    return app.exec()