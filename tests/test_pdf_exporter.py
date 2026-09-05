from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pymupdf

from registrydesk.domain.exporting import DEFAULT_EXPORT_FIELDS
from registrydesk.domain.registry import RegistryDetails, RegistryRow
from registrydesk.presentation.pdf import PdfExporter


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


def test_pdf_exporter_writes_two_decimal_areas_and_exact_share_fractions(tmp_path: Path) -> None:
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
    path = tmp_path / "out.pdf"

    PdfExporter().export(details, DEFAULT_EXPORT_FIELDS, path)

    document = pymupdf.open(path)
    text = "\n".join(page.get_text("text") for page in document)
    document.close()

    assert "КВАРТИРИ" in text
    assert "85.10" in text
    assert "28.37" in text
    assert "1/3" in text
    assert "56.73" in text
    assert "2/3" in text
