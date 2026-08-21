"""Export field and format definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExportField:
    key: str
    label: str
    property_level: bool = False
    header: str = ""

    @property
    def header_label(self) -> str:
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

EXPORT_FIELDS_BY_KEY = {field.key: field for field in EXPORT_FIELDS}
DEFAULT_EXPORT_FIELDS = (
    "unit_number",
    "total_area",
    "owner_no",
    "owner_name",
    "ownership_area",
    "share",
)

EXPORT_FORMATS: tuple[tuple[str, str], ...] = (
    ("xlsx", "Excel (.xlsx)"),
    ("pdf", "PDF (.pdf)"),
    ("csv", "CSV (.csv)"),
)
EXPORT_FORMAT_LABELS = dict(EXPORT_FORMATS)
