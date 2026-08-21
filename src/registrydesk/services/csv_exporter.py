"""CSV exporter for the clean owner view."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from registrydesk.domain.export import EXPORT_FIELDS_BY_KEY
from registrydesk.domain.registry import RegistryDetails
from registrydesk.services.export_values import plain_export_value


class CsvExporter:
    """Create a flat UTF-8 BOM CSV with one row per clean ownership row."""

    def export(self, registry: RegistryDetails, field_keys: Iterable[str], path: Path) -> None:
        keys = tuple(field_keys)
        if not keys:
            raise ValueError("Потрібно вибрати хоча б одне поле для експорту.")
        unknown = [key for key in keys if key not in EXPORT_FIELDS_BY_KEY]
        if unknown:
            raise ValueError(f"Невідомі поля експорту: {', '.join(unknown)}")

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.writer(file, delimiter=";", quoting=csv.QUOTE_MINIMAL)
            writer.writerow([EXPORT_FIELDS_BY_KEY[key].header_label for key in keys])
            decimal_comma_fields = {"total_area", "living_area", "ownership_area", "share"}
            for sequence, row in enumerate(registry.rows, start=1):
                values = []
                for key in keys:
                    value = plain_export_value(key, row, sequence)
                    if key in decimal_comma_fields:
                        value = value.replace(".", ",")
                    values.append(value)
                writer.writerow(values)
