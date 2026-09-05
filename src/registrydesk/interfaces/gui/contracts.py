"""Typed GUI column contracts."""

from enum import IntEnum


class _LabeledColumn(IntEnum):
    """Integer column contract carrying its user-facing header label."""

    def __new__(cls, value: int, label: str) -> "_LabeledColumn":
        member = int.__new__(cls, value)
        member._value_ = value
        member.label = label
        return member

    label: str


class RegistryListColumn(_LabeledColumn):
    """Columns shown in the imported-registry start page."""

    FORMED_AT = (0, "Дата довідки")
    REFERENCE_NUMBER = (1, "№ довідки")
    ADDRESS = (2, "Адреса")
    PROPERTY_COUNT = (3, "Об’єктів")
    OWNER_COUNT = (4, "Власників")
    IMPORTED_AT = (5, "Імпортовано")


class RegistryTableColumn(_LabeledColumn):
    """Columns shown in the normalized owner/property table."""

    UNIT = (0, "№")
    OWNER = (1, "Власник")
    TOTAL_AREA = (2, "Загальна площа")
    SHARE = (3, "Частка")
    OWNERSHIP_AREA = (4, "Площа у власності")
    REGISTRY_NUMBER = (5, "Реєстраційний № об’єкта")
    RIGHT_RECORD_NUMBERS = (6, "№ запису(ів) про право")
