"""Thin GUI-facing application facade."""

from pathlib import Path

from registrydesk.domain.exporting import ExportFormat
from registrydesk.domain.registry import RegistryDetails, RegistrySummary
from registrydesk.services.registry import RegistryService


class RegistryApplication:
    """GUI-facing facade for RegistryDesk use cases.

    The interface layer depends on this facade and domain contracts only.
    Repository, SQLite, parser and presentation details stay below the
    application boundary so the GUI remains independent from implementation
    choices in lower layers.
    """

    def __init__(self, registry: RegistryService) -> None:
        self._registry = registry

    def import_pdf(self, path: Path) -> int:
        """Import one supported registry PDF and return its persistent id."""
        return self._registry.import_pdf(path)

    def list_registries(self) -> list[RegistrySummary]:
        """Return lightweight summaries for the registry start page."""
        return self._registry.list_registries()

    def get_registry(self, registry_id: int) -> RegistryDetails | None:
        """Return the normalized read view for one imported registry."""
        return self._registry.get_registry(registry_id)

    def delete_registry(self, registry_id: int) -> None:
        """Delete an imported registry snapshot and all of its child rows."""
        self._registry.delete_registry(registry_id)

    def export(
        self,
        registry_id: int,
        export_format: ExportFormat,
        field_keys: tuple[str, ...],
        path: Path,
    ) -> None:
        """Export a selected registry view using the requested field order."""
        self._registry.export(registry_id, export_format, field_keys, path)
