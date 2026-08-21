"""Domain objects for imported registry snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from fractions import Fraction
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RegistryDocumentDraft:
    source_filename: str
    source_sha256: str
    page_count: int
    information_reference_number: str
    formed_at: str
    formed_by: str
    formation_basis: str
    query_type: str
    query_address: str
    pages: tuple["RegistryPageDraft", ...]
    properties: tuple["PropertyDraft", ...]


@dataclass(frozen=True, slots=True)
class RegistryPageDraft:
    page_number: int
    text: str


@dataclass(frozen=True, slots=True)
class PropertyDraft:
    registry_number: str
    object_description: str
    object_type_raw: str
    object_type: str
    edessb_identifier: str
    total_area: Decimal
    living_area: Decimal | None
    address_raw: str
    building_number: str
    unit_type: str
    unit_number: str
    source_page_start: int
    source_page_end: int
    raw_text: str
    ownerships: tuple["OwnershipDraft", ...]


@dataclass(frozen=True, slots=True)
class OwnershipDraft:
    right_record_number: str
    right_type: str
    joint_ownership_type: str
    share_raw: str
    share_numerator: int | None
    share_denominator: int | None
    owner_name_raw: str
    owner_name: str
    owner_type: str
    legal_entity_code: str
    registration_country: str
    legacy_registration_raw: str
    legacy_registry_name: str
    legacy_record_number: str
    legacy_registered_at: str
    source_page: int
    raw_text: str

    @property
    def explicit_share(self) -> Fraction | None:
        if self.share_numerator is None or self.share_denominator is None:
            return None
        return Fraction(self.share_numerator, self.share_denominator)


@dataclass(frozen=True, slots=True)
class RegistrySummary:
    id: int
    source_filename: str
    information_reference_number: str
    formed_at: str
    query_address: str
    page_count: int
    property_count: int
    owner_count: int
    imported_at: str

    @property
    def display_name(self) -> str:
        number = self.information_reference_number or "без номера"
        return f"{self.query_address} — № {number}" if self.query_address else f"Довідка № {number}"


@dataclass(frozen=True, slots=True)
class RegistryRow:
    property_id: int
    unit_number: str
    property_type: str
    property_type_raw: str
    owner_name: str
    owner_type: str
    total_area: Decimal
    living_area: Decimal | None
    share: Fraction
    registry_number: str
    right_record_numbers: tuple[str, ...]
    right_type: str
    joint_ownership_type: str
    edessb_identifier: str
    address: str
    legal_entity_code: str
    registration_country: str

    @property
    def ownership_area(self) -> Decimal:
        return self.total_area * Decimal(self.share.numerator) / Decimal(self.share.denominator)

    @property
    def share_text(self) -> str:
        if self.share.denominator == 1:
            return str(self.share.numerator)
        return f"{self.share.numerator}/{self.share.denominator}"


@dataclass(frozen=True, slots=True)
class RegistryDetails:
    id: int
    source_filename: str
    information_reference_number: str
    formed_at: str
    formed_by: str
    formation_basis: str
    query_type: str
    query_address: str
    page_count: int
    imported_at: str
    rows: tuple[RegistryRow, ...] = field(default_factory=tuple)


class RegistryImportError(ValueError):
    """Raised when a PDF cannot be parsed as a supported CNAP registry extract."""


class DuplicateRegistryError(ValueError):
    """Raised when the same source document has already been imported."""
