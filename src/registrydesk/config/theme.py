"""Theme selection read once during application startup."""

from enum import StrEnum


class Theme(StrEnum):
    """Supported startup appearance modes.

    ``SYSTEM`` leaves the palette decision to Qt/the operating system; LIGHT
    and DARK only select the corresponding RegistryDesk stylesheet overlay.
    """

    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"

    @classmethod
    def from_value(cls, value: str | None) -> "Theme":
        """Parse an environment value, falling back to ``system`` when invalid."""
        if value is None:
            return cls.SYSTEM
        try:
            return cls(value.strip().casefold())
        except ValueError:
            return cls.SYSTEM
