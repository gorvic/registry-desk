"""Environment-backed application settings."""

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

from registrydesk.config.theme import Theme


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Startup-only settings loaded from ``.env`` with safe defaults."""

    theme: Theme = Theme.SYSTEM

    @classmethod
    def load(cls, root: Path) -> "AppSettings":
        """Load settings once at startup; runtime theme changes are unsupported."""
        # ``override=False`` lets an explicitly supplied process environment win
        # over a local .env file, which is useful for packaged deployments/tests.
        load_dotenv(root / ".env", override=False)
        return cls(theme=Theme.from_value(os.getenv("THEME")))
