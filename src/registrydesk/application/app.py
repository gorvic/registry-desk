"""Application use cases."""

from __future__ import annotations

from pathlib import Path

from registrydesk.domain.registry import RegistryDetails, RegistrySummary
from registrydesk.repositories import SQLiteRegistryRepository
from registrydesk.services import CnapPdfImporter, CsvExporter, PdfExporter, XlsxExporter


class RegistryApplication:
    """Coordinate immutable registry imports, reads, deletes, and exports."""

    def __init__(
        self,
        repository: SQLiteRegistryRepository,
        importer: CnapPdfImporter,
        xlsx_exporter: XlsxExporter,
        csv_exporter: CsvExporter,
        pdf_exporter: PdfExporter,
    ) -> None:
        self._repository = repository
        self._importer = importer
        self._exporters = {
            "xlsx": xlsx_exporter,
            "csv": csv_exporter,
            "pdf": pdf_exporter,
        }

    def import_pdf(self, path: Path) -> int:
        draft = self._importer.parse(path)
        return self._repository.create(draft)

    def list_registries(self) -> list[RegistrySummary]:
        return self._repository.list_summaries()

    def get_registry(self, registry_id: int) -> RegistryDetails | None:
        return self._repository.get_details(registry_id)

    def delete_registry(self, registry_id: int) -> None:
        self._repository.delete(registry_id)

    def export(
        self,
        registry_id: int,
        export_format: str,
        field_keys: tuple[str, ...],
        path: Path,
    ) -> None:
        registry = self._repository.get_details(registry_id)
        if registry is None:
            raise ValueError("Реєстр не знайдено.")
        exporter = self._exporters.get(export_format)
        if exporter is None:
            raise ValueError(f"Непідтримуваний формат експорту: {export_format}")
        exporter.export(registry, field_keys, path)

    def export_xlsx(self, registry_id: int, field_keys: tuple[str, ...], path: Path) -> None:
        self.export(registry_id, "xlsx", field_keys, path)

    def export_csv(self, registry_id: int, field_keys: tuple[str, ...], path: Path) -> None:
        self.export(registry_id, "csv", field_keys, path)

    def export_pdf(self, registry_id: int, field_keys: tuple[str, ...], path: Path) -> None:
        self.export(registry_id, "pdf", field_keys, path)
