"""Export fields and formats used by the clean ownership view."""

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

from registrydesk.domain.errors import ErrorMessage, ExportError
from typing import Iterable, Mapping


class ExportFormat(StrEnum):
    """Export format plus the GUI/file metadata owned by that contract."""

    XLSX = ("xlsx", "Excel (.xlsx)", ".xlsx", "Excel (*.xlsx)")
    PDF = ("pdf", "PDF (.pdf)", ".pdf", "PDF (*.pdf)")
    CSV = ("csv", "CSV (.csv)", ".csv", "CSV (*.csv)")

    def __new__(
        cls,
        value: str,
        label: str,
        extension: str,
        file_filter: str,
    ) -> "ExportFormat":
        member = str.__new__(cls, value)
        member._value_ = value
        member.label = label
        member.extension = extension
        member.file_filter = file_filter
        return member

    label: str
    extension: str
    file_filter: str


@dataclass(frozen=True, slots=True)
class ExportField:
    """One selectable column in the normalized ownership export view."""

    key: str
    label: str
    property_level: bool = False
    header: str = ""

    @property
    def header_label(self) -> str:
        """Return the compact header override when one is defined."""
        return self.header or self.label


EXPORT_FIELDS: tuple[ExportField, ...] = (
    ExportField("unit_number", "№ квартири/приміщення", True, "№ пр."),
    ExportField("property_type", "Тип", True),
    ExportField("owner_no", "№"),
    ExportField("owner_name", "Власник"),
    ExportField("ownership_area", "Площа у власності"),
    ExportField("share", "Частка"),
    ExportField("total_area", "Загальна площа", True),
    ExportField("living_area", "Житлова площа", True),
    ExportField("registry_number", "Реєстраційний № об’єкта", True),
    ExportField("right_record_numbers", "№ запису(ів) про право"),
    ExportField("right_type", "Тип речового права"),
    ExportField("joint_ownership_type", "Вид спільної власності"),
    ExportField("edessb_identifier", "Ідентифікатор ЄДЕССБ", True),
    ExportField("address", "Адреса", True),
    ExportField("owner_type", "Тип власника"),
    ExportField("legal_entity_code", "Код ЄДРПОУ"),
    ExportField("registration_country", "Країна реєстрації"),
)
EXPORT_FIELDS_BY_KEY: Mapping[str, ExportField] = MappingProxyType(
    {field.key: field for field in EXPORT_FIELDS}
)
DEFAULT_EXPORT_FIELDS = (
    "unit_number",
    "total_area",
    "owner_no",
    "owner_name",
    "ownership_area",
    "share",
)


def validate_export_fields(field_keys: Iterable[str]) -> tuple[str, ...]:
    """Validate field keys once and preserve the caller-selected column order."""
    keys = tuple(field_keys)
    if not keys:
        raise ExportError(ErrorMessage.EXPORT_FIELDS_REQUIRED)
    unknown = [key for key in keys if key not in EXPORT_FIELDS_BY_KEY]
    if unknown:
        raise ExportError(ErrorMessage.EXPORT_FIELDS_UNKNOWN.format(items=", ".join(unknown)))
    return keys
