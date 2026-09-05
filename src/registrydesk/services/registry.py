"""Registry workflows independent from GUI and storage details."""

from pathlib import Path

from registrydesk.domain.errors import ErrorMessage, NotFoundError
from registrydesk.domain.exporting import ExportFormat
from registrydesk.domain.registry import RegistryDetails, RegistrySummary
from registrydesk.repositories.registry import SQLiteRegistryRepository
from registrydesk.services.exporting.service import ExportService


class RegistryService:
    """Coordinate registry import, persistence, retrieval and export.

    This service is the single use-case boundary below ``RegistryApplication``.
    It deliberately keeps heavyweight PDF parsing out of the normal startup
    path and delegates persistence/export details to their dedicated adapters.
    """

    def __init__(
        self,
        repository: SQLiteRegistryRepository,
        export_service: ExportService,
    ) -> None:
        self._repository = repository
        self._export_service = export_service

    def import_pdf(self, path: Path) -> int:
        """Parse and atomically persist one CNAP registry PDF."""
        # PyMuPDF is intentionally outside the normal startup path.
        from registrydesk.services.importing.pdf_importer import CnapPdfImporter

        return self._repository.create(CnapPdfImporter().parse(path))

    def list_registries(self) -> list[RegistrySummary]:
        """Return registry summaries ordered for the start page."""
        return self._repository.list_summaries()

    def get_registry(self, registry_id: int) -> RegistryDetails | None:
        """Return the normalized ownership view for a registry id."""
        return self._repository.get_details(registry_id)

    def delete_registry(self, registry_id: int) -> None:
        """Delete a complete imported registry snapshot."""
        self._repository.delete(registry_id)

    def export(
        self,
        registry_id: int,
        export_format: ExportFormat,
        field_keys: tuple[str, ...],
        path: Path,
    ) -> None:
        """Render one persisted registry using a validated export contract."""
        registry = self._repository.get_details(registry_id)
        if registry is None:
            raise NotFoundError(ErrorMessage.REGISTRY_NOT_FOUND)
        self._export_service.export(registry, export_format, field_keys, path)
