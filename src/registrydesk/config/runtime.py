"""Filesystem paths for source and frozen execution."""

from dataclasses import dataclass
from pathlib import Path
import sys


@dataclass(frozen=True, slots=True)
class RuntimePaths:
    """Resolved filesystem locations for source and frozen executions.

    User data lives beside the application root in ``.data`` for this small
    local utility.  Keeping path discovery in one value object prevents GUI,
    storage and packaging code from making conflicting cwd assumptions.
    """

    root: Path
    data_dir: Path
    database_path: Path

    @classmethod
    def discover(cls) -> "RuntimePaths":
        """Resolve the application root without depending on the current cwd."""
        if getattr(sys, "frozen", False):
            root = Path(sys.executable).resolve().parent
        else:
            root = Path(__file__).resolve().parents[3]
        data_dir = root / ".data"
        return cls(root=root, data_dir=data_dir, database_path=data_dir / "registrydesk.db")
