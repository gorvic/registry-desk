"""Runtime paths and single-instance protection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

from PySide6.QtCore import QSharedMemory

DEFAULT_SHARED_MEMORY_KEY = "registrydesk.application.single-instance"


class SingleInstanceGuard:
    def __init__(self, key: str = DEFAULT_SHARED_MEMORY_KEY) -> None:
        self._memory = QSharedMemory(key)
        self._acquired = False

    def acquire(self) -> bool:
        if not self._acquired:
            self._acquired = self._memory.create(1)
        return self._acquired

    def release(self) -> None:
        if self._acquired and self._memory.isAttached():
            self._memory.detach()
        self._acquired = False


@dataclass(frozen=True, slots=True)
class RuntimePaths:
    root: Path
    data_dir: Path
    database_path: Path

    @classmethod
    def discover(cls) -> "RuntimePaths":
        if getattr(sys, "frozen", False):
            root = Path(sys.executable).resolve().parent
        else:
            root = Path(__file__).resolve().parents[2]
        data_dir = root / ".data"
        return cls(root=root, data_dir=data_dir, database_path=data_dir / "registrydesk.db")


def run() -> int:
    guard = SingleInstanceGuard()
    if not guard.acquire():
        return 0
    try:
        from registrydesk.gui import run as run_gui

        return run_gui()
    finally:
        guard.release()
