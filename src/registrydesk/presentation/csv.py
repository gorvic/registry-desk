"""CSV exporter for the clean owner view."""

import csv
from pathlib import Path
from typing import Iterable

from registrydesk.domain.exporting import EXPORT_FIELDS_BY_KEY, validate_export_fields
from registrydesk.domain.registry import RegistryDetails
from registrydesk.presentation.values import plain_export_value


class CsvExporter:
    """Create a flat UTF-8 BOM CSV with one row per clean ownership row."""

    def export(self, registry: RegistryDetails, field_keys: Iterable[str], path: Path) -> None:
        """Write the selected clean view as semicolon-separated UTF-8 BOM CSV."""
        keys = validate_export_fields(field_keys)

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.writer(file, delimiter=";", quoting=csv.QUOTE_MINIMAL)
            writer.writerow([EXPORT_FIELDS_BY_KEY[key].header_label for key in keys])
            # Spreadsheet-oriented Ukrainian CSV convention expects decimal
            # commas while the shared value formatter deliberately stays neutral.
            decimal_comma_fields = {"total_area", "living_area", "ownership_area", "share"}
            for sequence, row in enumerate(registry.rows, start=1):
                values = []
                for key in keys:
                    value = plain_export_value(key, row, sequence)
                    if key in decimal_comma_fields:
                        value = value.replace(".", ",")
                    values.append(value)
                writer.writerow(values)
