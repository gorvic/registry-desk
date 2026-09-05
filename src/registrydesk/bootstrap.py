"""Explicit dependency assembly for the local application."""

from dataclasses import dataclass

from registrydesk.application import RegistryApplication
from registrydesk.config.runtime import RuntimePaths
from registrydesk.repositories import SQLiteRegistryRepository
from registrydesk.services.exporting import ExportService
from registrydesk.services.registry import RegistryService
from registrydesk.storage import Database


@dataclass(frozen=True, slots=True)
class BootstrapResult:
    """Objects needed by the interface after dependency composition completes."""

    app: RegistryApplication
    paths: RuntimePaths


def bootstrap() -> BootstrapResult:
    """Compose the local application explicitly from its concrete adapters."""
    paths = RuntimePaths.discover()
    paths.data_dir.mkdir(parents=True, exist_ok=True)

    database = Database(paths.database_path)
    database.initialize()
    repository = SQLiteRegistryRepository(database)
    registry = RegistryService(repository, ExportService())
    return BootstrapResult(RegistryApplication(registry), paths)
