"""GUI file-dialog helpers and export filename normalization."""

from pathlib import Path
import re

from PySide6.QtWidgets import QFileDialog, QWidget

from registrydesk.domain import ExportFormat


def choose_import_pdf(parent: QWidget) -> Path | None:
    """Return the selected PDF path, or ``None`` when the dialog is cancelled."""
    filename, _ = QFileDialog.getOpenFileName(
        parent,
        "Імпорт довідки ЦНАП",
        "",
        "PDF (*.pdf)",
    )
    return Path(filename) if filename else None


def choose_export_path(
    parent: QWidget,
    export_format: ExportFormat,
    suggested: str,
) -> Path | None:
    """Choose an output path and normalize it to the selected extension."""
    filename, _ = QFileDialog.getSaveFileName(
        parent,
        "Експорт",
        suggested,
        export_format.file_filter,
    )
    if not filename:
        return None
    path = Path(filename)
    return path if path.suffix.casefold() == export_format.extension else path.with_suffix(
        export_format.extension
    )


def suggest_export_name(address: str, export_format: ExportFormat) -> str:
    """Build a filesystem-safe, address-derived default export filename."""
    text = address or "registry"
    text = re.sub(r"^(м\.?Київ|місто Київ),\s*", "", text, flags=re.I)
    text = text.replace("вулиця ", "").replace("будинок ", "")
    text = re.sub(r"[^0-9A-Za-zА-Яа-яІіЇїЄєҐґ._ -]+", "_", text)
    text = re.sub(r"\s+", "_", text).strip("_.")
    return f"{text or 'registry'}_власники{export_format.extension}"
