"""SQLite connection and migration management."""

import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Iterator

from registrydesk.storage.migrations import MIGRATIONS


class Database:
    """Small SQLite gateway with explicit transactions and migrations."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def initialize(self) -> None:
        """Create the database directory and apply pending forward migrations."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as connection:
            current = int(connection.execute("PRAGMA user_version").fetchone()[0])
            for migration in MIGRATIONS:
                if migration.version <= current:
                    # ``user_version`` is the entire migration state for this
                    # local SQLite utility; already-applied scripts stay inert.
                    continue
                try:
                    connection.executescript(
                        "BEGIN;\n"
                        + migration.sql
                        + f"\nPRAGMA user_version = {migration.version};\nCOMMIT;"
                    )
                except Exception:
                    connection.rollback()
                    raise
                current = migration.version

    def connect(self) -> sqlite3.Connection:
        """Open a configured SQLite connection with rows addressable by name."""
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Yield one explicit transaction that commits or rolls back as a unit."""
        connection = self.connect()
        try:
            connection.execute("BEGIN")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
