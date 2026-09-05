"""Stable domain contracts shared across RegistryDesk layers."""

from enum import StrEnum


class OwnerType(StrEnum):
    """Normalized owner categories preserved across import, storage and export."""

    INDIVIDUAL = "фізична особа"
    LEGAL_ENTITY = "юридична особа"


class PropertyType(StrEnum):
    """Canonical property type used for display, grouping and natural sorting."""

    APARTMENT = "квартира"
    PREMISES = "приміщення"
    OTHER = "інше"

    @property
    def abbreviation(self) -> str:
        """Return the compact Ukrainian label used by narrow UI/export cells."""
        return {
            PropertyType.APARTMENT: "кв.",
            PropertyType.PREMISES: "прим.",
            PropertyType.OTHER: "інше",
        }[self]

    @property
    def sort_order(self) -> int:
        """Return the stable domain order: apartments, premises, then other."""
        return {
            PropertyType.APARTMENT: 0,
            PropertyType.PREMISES: 1,
            PropertyType.OTHER: 2,
        }[self]

    @classmethod
    def from_value(cls, value: str) -> "PropertyType":
        """Normalize an unknown persisted/parser value to ``OTHER`` safely."""
        try:
            return cls(value)
        except ValueError:
            return cls.OTHER
