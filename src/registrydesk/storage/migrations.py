"""Forward database migrations."""

from dataclasses import dataclass

from registrydesk.storage.schema import SCHEMA_SQL


@dataclass(frozen=True, slots=True)
class Migration:
    version: int
    sql: str


MIGRATIONS = (Migration(1, SCHEMA_SQL),)
