"""Apply the startup-selected theme to the Qt application."""

from pathlib import Path

from PySide6.QtWidgets import QApplication

from registrydesk.config import Theme


def apply_theme(app: QApplication, theme: Theme, resources_dir: Path) -> None:
    """Apply base QSS plus the optional startup-selected light/dark overlay."""
    styles_dir = resources_dir / "styles"
    parts = [_read_optional(styles_dir / "base.qss")]
    # SYSTEM deliberately adds no palette override: Qt follows the operating
    # system for this process lifetime.  Theme changes require an app restart.
    if theme is Theme.LIGHT:
        parts.append(_read_optional(styles_dir / "light.qss"))
    elif theme is Theme.DARK:
        parts.append(_read_optional(styles_dir / "dark.qss"))
    app.setStyleSheet("\n".join(part for part in parts if part))


def _read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""
