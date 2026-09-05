"""Domain objects for imported registry snapshots."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from fractions import Fraction


@dataclass(frozen=True, slots=True)
class RegistryDocumentDraft:
    """Complete immutable parser result before persistence."""

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
    """Source page text retained for traceability and future parser diagnostics."""

    page_number: int
    text: str


@dataclass(frozen=True, slots=True)
class PropertyDraft:
    """Normalized property plus its source-level ownership records."""

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
    """One parsed right/owner record before repository cleanup and grouping."""

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
        """Return the explicitly stated share, or ``None`` when PDF omitted it."""
        if self.share_numerator is None or self.share_denominator is None:
            return None
        return Fraction(self.share_numerator, self.share_denominator)


@dataclass(frozen=True, slots=True)
class RegistrySummary:
    """Lightweight registry metadata used by the start-page list."""

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
        """Build the compact human-readable label used by the GUI."""
        number = self.information_reference_number or "без номера"
        return f"{self.query_address} — № {number}" if self.query_address else f"Довідка № {number}"


@dataclass(frozen=True, slots=True)
class RegistryRow:
    """Clean owner/property row used by the GUI and export renderers."""

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
        """Derive owned area from canonical total area and exact fractional share."""
        return self.total_area * Decimal(self.share.numerator) / Decimal(self.share.denominator)

    @property
    def share_text(self) -> str:
        """Render the exact ownership share without decimal precision loss."""
        return str(self.share.numerator) if self.share.denominator == 1 \
            else f"{self.share.numerator}/{self.share.denominator}"


@dataclass(frozen=True, slots=True)
class RegistryDetails:
    """Full read model for one imported registry snapshot."""

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
