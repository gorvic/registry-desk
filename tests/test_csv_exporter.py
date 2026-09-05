import csv
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

from registrydesk.domain.registry import RegistryDetails, RegistryRow
from registrydesk.presentation.csv import CsvExporter


def _row(owner: str, share: Fraction) -> RegistryRow:
    return RegistryRow(
        property_id=1,
        unit_number="129",
        property_type="квартира",
        property_type_raw="квартира",
        owner_name=owner,
        owner_type="фізична особа",
        total_area=Decimal("85.1"),
        living_area=Decimal("48.0"),
        share=share,
        registry_number="100",
        right_record_numbers=("1",),
        right_type="право власності",
        joint_ownership_type="спільна часткова",
        edessb_identifier="",
        address="м.Київ, вулиця Тестова, будинок 1, квартира 129",
        legal_entity_code="",
        registration_country="",
    )


def test_csv_exporter_writes_smart_calculated_decimals(tmp_path: Path) -> None:
    details = RegistryDetails(
        id=1,
        source_filename="test.pdf",
        information_reference_number="1",
        formed_at="",
        formed_by="",
        formation_basis="",
        query_type="",
        query_address="м.Київ, вулиця Тестова, будинок 1",
        page_count=1,
        imported_at="",
        rows=(_row("Перший", Fraction(1, 3)), _row("Другий", Fraction(2, 3))),
    )
    path = tmp_path / "out.csv"

    CsvExporter().export(
        details,
        ("unit_number", "owner_name", "total_area", "ownership_area", "share"),
        path,
    )

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.reader(file, delimiter=";"))

    assert rows[1] == ["129", "Перший", "85,1", "28,366666666667", "0,333333333333"]
    assert rows[2] == ["129", "Другий", "85,1", "56,733333333333", "0,666666666667"]
