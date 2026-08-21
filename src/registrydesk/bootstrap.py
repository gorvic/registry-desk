"""Dependency assembly."""

from dataclasses import dataclass

from registrydesk.application import RegistryApplication
from registrydesk.repositories import SQLiteRegistryRepository
from registrydesk.runtime import RuntimePaths
from registrydesk.services import CnapPdfImporter, CsvExporter, PdfExporter, XlsxExporter
from registrydesk.storage import Database


@dataclass(frozen=True, slots=True)
class BootstrapResult:
    app: RegistryApplication
    paths: RuntimePaths


def bootstrap() -> BootstrapResult:
    paths = RuntimePaths.discover()
    paths.data_dir.mkdir(parents=True, exist_ok=True)
    database = Database(paths.database_path)
    database.initialize()
    app = RegistryApplication(
        SQLiteRegistryRepository(database),
        CnapPdfImporter(),
        XlsxExporter(),
        CsvExporter(),
        PdfExporter(),
    )
    return BootstrapResult(app, paths)
