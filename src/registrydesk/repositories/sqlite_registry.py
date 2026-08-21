"""SQLite repository for immutable imported registry snapshots."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from fractions import Fraction

from registrydesk.domain.registry import (
    DuplicateRegistryError,
    RegistryDetails,
    RegistryDocumentDraft,
    RegistryRow,
    RegistrySummary,
)
from registrydesk.storage import Database


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")




_UKRAINIAN_ALPHABET = "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
_UKRAINIAN_ORDER = {char: index + 100 for index, char in enumerate(_UKRAINIAN_ALPHABET)}


def _ukrainian_text_key(value: str) -> tuple[int, ...]:
    result: list[int] = []
    for char in value.casefold():
        if char.isspace():
            result.append(0)
        elif char in _UKRAINIAN_ORDER:
            result.append(_UKRAINIAN_ORDER[char])
        else:
            result.append(1000 + ord(char))
    return tuple(result)

def _natural_key(value: str) -> tuple:
    import re

    parts = re.split(r"(\d+)", value.casefold())
    return tuple(int(part) if part.isdigit() else part for part in parts)


class SQLiteRegistryRepository:
    """Persist source-level records and expose a normalized read-only owner view."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def create(self, draft: RegistryDocumentDraft) -> int:
        with self._database.transaction() as connection:
            existing = connection.execute(
                "SELECT id FROM registries WHERE source_sha256 = ?", (draft.source_sha256,)
            ).fetchone()
            if existing is not None:
                raise DuplicateRegistryError("Цю PDF-довідку вже імпортовано.")

            cursor = connection.execute(
                """
                INSERT INTO registries (
                    source_filename, source_sha256, page_count,
                    information_reference_number, formed_at, formed_by,
                    formation_basis, query_type, query_address, imported_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    draft.source_filename,
                    draft.source_sha256,
                    draft.page_count,
                    draft.information_reference_number,
                    draft.formed_at,
                    draft.formed_by,
                    draft.formation_basis,
                    draft.query_type,
                    draft.query_address,
                    _now_iso(),
                ),
            )
            registry_id = int(cursor.lastrowid)

            connection.executemany(
                "INSERT INTO registry_pages (registry_id, page_number, text) VALUES (?, ?, ?)",
                ((registry_id, page.page_number, page.text) for page in draft.pages),
            )

            for prop in draft.properties:
                prop_cursor = connection.execute(
                    """
                    INSERT INTO properties (
                        registry_id, registry_number, object_description,
                        object_type_raw, object_type, edessb_identifier,
                        total_area, living_area, address_raw, building_number,
                        unit_type, unit_number, source_page_start, source_page_end, raw_text
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        registry_id,
                        prop.registry_number,
                        prop.object_description,
                        prop.object_type_raw,
                        prop.object_type,
                        prop.edessb_identifier,
                        str(prop.total_area),
                        str(prop.living_area) if prop.living_area is not None else None,
                        prop.address_raw,
                        prop.building_number,
                        prop.unit_type,
                        prop.unit_number,
                        prop.source_page_start,
                        prop.source_page_end,
                        prop.raw_text,
                    ),
                )
                property_id = int(prop_cursor.lastrowid)
                connection.executemany(
                    """
                    INSERT INTO ownerships (
                        property_id, right_record_number, right_type,
                        joint_ownership_type, share_raw, share_numerator, share_denominator,
                        owner_name_raw, owner_name, owner_type, legal_entity_code,
                        registration_country, legacy_registration_raw, legacy_registry_name,
                        legacy_record_number, legacy_registered_at, source_page, raw_text
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        (
                            property_id,
                            own.right_record_number,
                            own.right_type,
                            own.joint_ownership_type,
                            own.share_raw,
                            own.share_numerator,
                            own.share_denominator,
                            own.owner_name_raw,
                            own.owner_name,
                            own.owner_type,
                            own.legal_entity_code,
                            own.registration_country,
                            own.legacy_registration_raw,
                            own.legacy_registry_name,
                            own.legacy_record_number,
                            own.legacy_registered_at,
                            own.source_page,
                            own.raw_text,
                        )
                        for own in prop.ownerships
                    ),
                )
        return registry_id

    def list_summaries(self) -> list[RegistrySummary]:
        with self._database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    r.*,
                    COUNT(DISTINCT p.id) AS property_count,
                    COUNT(DISTINCT CASE
                        WHEN o.legal_entity_code <> '' THEN 'legal:' || o.legal_entity_code
                        ELSE 'name:' || lower(o.owner_name)
                    END) AS owner_count
                FROM registries r
                LEFT JOIN properties p ON p.registry_id = r.id
                LEFT JOIN ownerships o ON o.property_id = p.id
                GROUP BY r.id
                ORDER BY r.imported_at DESC, r.id DESC
                """
            ).fetchall()
        return [
            RegistrySummary(
                id=int(row["id"]),
                source_filename=row["source_filename"],
                information_reference_number=row["information_reference_number"],
                formed_at=row["formed_at"],
                query_address=row["query_address"],
                page_count=int(row["page_count"]),
                property_count=int(row["property_count"]),
                owner_count=int(row["owner_count"]),
                imported_at=row["imported_at"],
            )
            for row in rows
        ]

    def delete(self, registry_id: int) -> None:
        with self._database.transaction() as connection:
            connection.execute("DELETE FROM registries WHERE id = ?", (registry_id,))

    def get_details(self, registry_id: int) -> RegistryDetails | None:
        with self._database.connect() as connection:
            registry = connection.execute(
                "SELECT * FROM registries WHERE id = ?", (registry_id,)
            ).fetchone()
            if registry is None:
                return None

            records = connection.execute(
                """
                SELECT
                    p.id AS property_id,
                    p.registry_number,
                    p.object_type_raw,
                    p.object_type,
                    p.edessb_identifier,
                    p.total_area,
                    p.living_area,
                    p.address_raw,
                    p.unit_type,
                    p.unit_number,
                    o.right_record_number,
                    o.right_type,
                    o.joint_ownership_type,
                    o.share_numerator,
                    o.share_denominator,
                    o.owner_name,
                    o.owner_type,
                    o.legal_entity_code,
                    o.registration_country
                FROM properties p
                JOIN ownerships o ON o.property_id = p.id
                WHERE p.registry_id = ?
                ORDER BY p.id, o.id
                """,
                (registry_id,),
            ).fetchall()

        grouped: dict[tuple[int, str], list] = defaultdict(list)
        for row in records:
            owner_key = (
                f"legal:{row['legal_entity_code']}"
                if row["legal_entity_code"]
                else f"name:{str(row['owner_name']).casefold()}"
            )
            grouped[(int(row["property_id"]), owner_key)].append(row)

        clean_rows: list[RegistryRow] = []
        for owner_records in grouped.values():
            first = owner_records[0]
            shares: list[Fraction] = []
            for row in owner_records:
                numerator = row["share_numerator"]
                denominator = row["share_denominator"]
                if numerator is None or denominator is None:
                    shares.append(Fraction(1, 1))
                else:
                    shares.append(Fraction(int(numerator), int(denominator)))
            share = sum(shares, Fraction(0, 1))
            clean_rows.append(
                RegistryRow(
                    property_id=int(first["property_id"]),
                    unit_number=first["unit_number"],
                    property_type=first["unit_type"] or first["object_type"],
                    property_type_raw=first["object_type_raw"],
                    owner_name=first["owner_name"],
                    owner_type=first["owner_type"],
                    total_area=Decimal(first["total_area"]),
                    living_area=Decimal(first["living_area"]) if first["living_area"] else None,
                    share=share,
                    registry_number=first["registry_number"],
                    right_record_numbers=tuple(
                        str(row["right_record_number"])
                        for row in owner_records
                        if row["right_record_number"]
                    ),
                    right_type=first["right_type"],
                    joint_ownership_type=first["joint_ownership_type"],
                    edessb_identifier=first["edessb_identifier"],
                    address=first["address_raw"],
                    legal_entity_code=first["legal_entity_code"],
                    registration_country=first["registration_country"],
                )
            )

        type_rank = {"квартира": 0, "приміщення": 1}
        clean_rows.sort(
            key=lambda row: (
                type_rank.get(row.property_type, 2),
                _natural_key(row.unit_number),
                _ukrainian_text_key(row.owner_name),
            )
        )

        return RegistryDetails(
            id=int(registry["id"]),
            source_filename=registry["source_filename"],
            information_reference_number=registry["information_reference_number"],
            formed_at=registry["formed_at"],
            formed_by=registry["formed_by"],
            formation_basis=registry["formation_basis"],
            query_type=registry["query_type"],
            query_address=registry["query_address"],
            page_count=int(registry["page_count"]),
            imported_at=registry["imported_at"],
            rows=tuple(clean_rows),
        )
