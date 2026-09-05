from decimal import Decimal
from pathlib import Path

from registrydesk.domain.registry import OwnershipDraft, PropertyDraft, RegistryDocumentDraft, RegistryPageDraft
from registrydesk.repositories import SQLiteRegistryRepository
from registrydesk.storage import Database


def ownership(number: str, name: str, numerator: int, denominator: int) -> OwnershipDraft:
    return OwnershipDraft(
        right_record_number=number,
        right_type="право власності",
        joint_ownership_type="спільна часткова",
        share_raw=f"{numerator}/{denominator}",
        share_numerator=numerator,
        share_denominator=denominator,
        owner_name_raw=name,
        owner_name=name,
        owner_type="фізична особа",
        legal_entity_code="",
        registration_country="",
        legacy_registration_raw="",
        legacy_registry_name="",
        legacy_record_number="",
        legacy_registered_at="",
        source_page=1,
        raw_text="raw",
    )


def test_repository_aggregates_multiple_rights_of_same_owner(tmp_path: Path) -> None:
    database = Database(tmp_path / "test.db")
    database.initialize()
    repo = SQLiteRegistryRepository(database)
    prop = PropertyDraft(
        registry_number="1",
        object_description="",
        object_type_raw="квартира",
        object_type="квартира",
        edessb_identifier="",
        total_area=Decimal("52"),
        living_area=Decimal("20"),
        address_raw="м.Київ, вулиця Тестова, будинок 1, квартира 1",
        building_number="1",
        unit_type="квартира",
        unit_number="1",
        source_page_start=1,
        source_page_end=1,
        raw_text="raw",
        ownerships=(ownership("11", "Іваненко Іван", 1, 2), ownership("12", "Іваненко Іван", 1, 2)),
    )
    draft = RegistryDocumentDraft(
        source_filename="test.pdf",
        source_sha256="abc",
        page_count=1,
        information_reference_number="123",
        formed_at="21.08.2026 12:00:00",
        formed_by="ЦНАП",
        formation_basis="Заява",
        query_type="права власності",
        query_address="м.Київ, вулиця Тестова, будинок 1",
        pages=(RegistryPageDraft(1, "raw"),),
        properties=(prop,),
    )

    registry_id = repo.create(draft)
    details = repo.get_details(registry_id)

    assert details is not None
    assert len(details.rows) == 1
    assert details.rows[0].share_text == "1"
    assert details.rows[0].right_record_numbers == ("11", "12")
