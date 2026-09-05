from decimal import Decimal
from fractions import Fraction
from pathlib import Path

from openpyxl import load_workbook

from registrydesk.domain.exporting import DEFAULT_EXPORT_FIELDS
from registrydesk.domain.registry import RegistryDetails, RegistryRow
from registrydesk.presentation.xlsx import XlsxExporter


def row(property_id: int, owner: str, share: Fraction) -> RegistryRow:
    return RegistryRow(
        property_id=property_id,
        unit_number="9",
        property_type="квартира",
        property_type_raw="квартира",
        owner_name=owner,
        owner_type="фізична особа",
        total_area=Decimal("85.3"),
        living_area=Decimal("48.2"),
        share=share,
        registry_number="100",
        right_record_numbers=(str(property_id),),
        right_type="право власності",
        joint_ownership_type="спільна часткова",
        edessb_identifier="",
        address="м.Київ, вулиця Тестова, будинок 1, квартира 9",
        legal_entity_code="",
        registration_country="",
    )


def test_exporter_merges_property_fields_and_writes_formulas(tmp_path: Path) -> None:
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
        rows=(row(1, "Перший", Fraction(9, 20)), row(1, "Другий", Fraction(11, 20))),
    )
    path = tmp_path / "out.xlsx"

    XlsxExporter().export(details, DEFAULT_EXPORT_FIELDS, path)

    workbook = load_workbook(path, data_only=False)
    sheet = workbook.active
    assert "A3:A4" in {str(item) for item in sheet.merged_cells.ranges}
    assert "B3:B4" in {str(item) for item in sheet.merged_cells.ranges}
    assert sheet["F3"].value == "=9/20"
    assert sheet["F4"].value == "=11/20"
    assert sheet["E3"].value == "=B3*F3"
    assert sheet["E4"].value == "=B3*F4"
    assert sheet["B3"].number_format == "0.00"
    assert sheet["E3"].number_format == "0.00"
    assert sheet["F3"].number_format == "0.00"
