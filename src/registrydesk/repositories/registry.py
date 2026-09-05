"""SQLite repository for immutable imported registry snapshots."""

from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from fractions import Fraction
import sqlite3

from registrydesk.common.sorting import natural_text_key, ukrainian_text_key
from registrydesk.domain.contracts import PropertyType
from registrydesk.domain.errors import DuplicateRegistryError, ErrorMessage
from registrydesk.domain.registry import (
    PropertyDraft,
    RegistryDetails,
    RegistryDocumentDraft,
    RegistryRow,
    RegistrySummary,
)
from registrydesk.storage import Database


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class SQLiteRegistryRepository:
    """Persist source-level rows and expose the normalized read-only owner view."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def create(self, draft: RegistryDocumentDraft) -> int:
        """Persist a parsed registry atomically and return its new identifier."""
        # A registry is meaningful only as a complete document.  Header, pages,
        # properties and ownerships therefore share one transaction so parser or
        # database failures can never leave a partially imported snapshot.
        with self._database.transaction() as connection:
            self._ensure_unique_source(connection, draft.source_sha256)
            registry_id = self._insert_registry(connection, draft)
            self._insert_pages(connection, registry_id, draft)
            self._insert_properties(connection, registry_id, draft.properties)
        return registry_id

    def list_summaries(self) -> list[RegistrySummary]:
        """Return compact summaries without loading full ownership rows."""
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
        return [self._summary(row) for row in rows]

    def get_details(self, registry_id: int) -> RegistryDetails | None:
        """Build the normalized read model for one persisted registry."""
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

        clean_rows = self._clean_rows(records)
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

    def delete(self, registry_id: int) -> None:
        """Delete one registry; SQLite cascades remove all dependent source rows."""
        with self._database.transaction() as connection:
            connection.execute("DELETE FROM registries WHERE id = ?", (registry_id,))

    @staticmethod
    def _ensure_unique_source(connection: sqlite3.Connection, source_sha256: str) -> None:
        existing = connection.execute(
            "SELECT id FROM registries WHERE source_sha256 = ?", (source_sha256,)
        ).fetchone()
        if existing is not None:
            raise DuplicateRegistryError(ErrorMessage.DUPLICATE_REGISTRY)

    @staticmethod
    def _insert_registry(connection: sqlite3.Connection, draft: RegistryDocumentDraft) -> int:
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
        return int(cursor.lastrowid)

    @staticmethod
    def _insert_pages(
        connection: sqlite3.Connection,
        registry_id: int,
        draft: RegistryDocumentDraft,
    ) -> None:
        connection.executemany(
            "INSERT INTO registry_pages (registry_id, page_number, text) VALUES (?, ?, ?)",
            ((registry_id, page.page_number, page.text) for page in draft.pages),
        )

    @classmethod
    def _insert_properties(
        cls,
        connection: sqlite3.Connection,
        registry_id: int,
        properties: tuple[PropertyDraft, ...],
    ) -> None:
        for prop in properties:
            cursor = connection.execute(
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
            cls._insert_ownerships(connection, int(cursor.lastrowid), prop)

    @staticmethod
    def _insert_ownerships(
        connection: sqlite3.Connection,
        property_id: int,
        prop: PropertyDraft,
    ) -> None:
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

    @staticmethod
    def _summary(row: sqlite3.Row) -> RegistrySummary:
        return RegistrySummary(
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

    @classmethod
    def _clean_rows(cls, records: list[sqlite3.Row]) -> list[RegistryRow]:
        """Collapse source right records into one clean row per property/owner."""
        grouped: dict[tuple[int, str], list[sqlite3.Row]] = defaultdict(list)
        for row in records:
            # Legal entities have a stable EDRPOU identifier.  Individuals do
            # not, so their normalized name is the best available grouping key.
            owner_key = (
                f"legal:{row['legal_entity_code']}"
                if row["legal_entity_code"]
                else f"name:{str(row['owner_name']).casefold()}"
            )
            grouped[(int(row["property_id"]), owner_key)].append(row)

        clean_rows = [cls._clean_row(items) for items in grouped.values()]
        clean_rows.sort(key=cls._row_sort_key)
        return clean_rows

    @staticmethod
    def _clean_row(records: list[sqlite3.Row]) -> RegistryRow:
        """Merge multiple rights for the same owner/property into one read row."""
        first = records[0]
        # The parser permits an omitted share only for a sole owner.  Repeating
        # that fallback here keeps persisted legacy/source rows safe to read.
        shares = [
            Fraction(1, 1)
            if row["share_numerator"] is None or row["share_denominator"] is None
            else Fraction(int(row["share_numerator"]), int(row["share_denominator"]))
            for row in records
        ]
        return RegistryRow(
            property_id=int(first["property_id"]),
            unit_number=first["unit_number"],
            property_type=first["unit_type"] or first["object_type"],
            property_type_raw=first["object_type_raw"],
            owner_name=first["owner_name"],
            owner_type=first["owner_type"],
            total_area=Decimal(first["total_area"]),
            living_area=Decimal(first["living_area"]) if first["living_area"] else None,
            share=sum(shares, Fraction(0, 1)),
            registry_number=first["registry_number"],
            right_record_numbers=tuple(
                str(row["right_record_number"]) for row in records if row["right_record_number"]
            ),
            right_type=first["right_type"],
            joint_ownership_type=first["joint_ownership_type"],
            edessb_identifier=first["edessb_identifier"],
            address=first["address_raw"],
            legal_entity_code=first["legal_entity_code"],
            registration_country=first["registration_country"],
        )

    @staticmethod
    def _row_sort_key(row: RegistryRow) -> tuple[object, ...]:
        """Apply the domain order and natural Ukrainian-aware presentation sort."""
        return (
            PropertyType.from_value(row.property_type).sort_order,
            natural_text_key(row.unit_number),
            ukrainian_text_key(row.owner_name),
        )
