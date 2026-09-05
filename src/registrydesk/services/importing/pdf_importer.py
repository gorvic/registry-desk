"""Parser for CNAP multi-apartment property registry PDF extracts."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import hashlib
from pathlib import Path
import re

import pymupdf

from registrydesk.domain.contracts import OwnerType, PropertyType
from registrydesk.domain.errors import RegistryImportError, RegistryImportMessage
from registrydesk.domain.registry import (
    OwnershipDraft,
    PropertyDraft,
    RegistryDocumentDraft,
    RegistryPageDraft,
)

PROPERTY_MARKER = "Актуальна інформація про об’єкт речових прав"
RIGHT_MARKER = "Номер відомостей про речове право:"
END_REGISTRY_MARKER = "З РЕЄСТРУ ПРАВ ВЛАСНОСТІ НА НЕРУХОМЕ МАЙНО"


@dataclass(frozen=True, slots=True)
class _Line:
    """One normalized PDF text line with its source page for diagnostics."""

    page: int
    text: str


def _compact(value: str) -> str:
    """Collapse layout whitespace emitted by PDF text extraction."""
    return re.sub(r"\s+", " ", value).strip()


def _join(lines: list[_Line] | tuple[_Line, ...]) -> str:
    """Preserve source line boundaries for stored diagnostic text."""
    return "\n".join(line.text for line in lines)


def _flat(lines: list[_Line] | tuple[_Line, ...]) -> str:
    """Flatten visual PDF lines before marker-based field extraction."""
    return _compact(" ".join(line.text for line in lines))


def _extract_between(text: str, start: str, end_patterns: tuple[str, ...]) -> str:
    """Extract text after a marker up to the nearest known following marker."""
    start_match = re.search(start, text, flags=re.IGNORECASE)
    if not start_match:
        return ""
    tail = text[start_match.end() :]
    nearest: int | None = None
    for pattern in end_patterns:
        match = re.search(pattern, tail, flags=re.IGNORECASE)
        if match is not None and (nearest is None or match.start() < nearest):
            nearest = match.start()
    return _compact(tail[:nearest] if nearest is not None else tail)


def _parse_decimal(value: str, field_name: str) -> Decimal:
    """Parse Ukrainian decimal notation without introducing float rounding."""
    try:
        return Decimal(value.replace(",", ".").strip())
    except (InvalidOperation, AttributeError) as exc:
        raise RegistryImportError(
            RegistryImportMessage.DECIMAL_PARSE.format(field=field_name, value=value)
        ) from exc


def _parse_share(raw: str) -> tuple[int | None, int | None]:
    """Normalize a textual ownership share to an exact numerator/denominator."""
    raw = raw.strip()
    if not raw:
        return None, None
    try:
        share = Fraction(raw)
    except (ValueError, ZeroDivisionError) as exc:
        raise RegistryImportError(RegistryImportMessage.INVALID_SHARE.format(value=raw)) from exc
    return share.numerator, share.denominator


def _normalize_property_type(raw: str, address: str) -> tuple[str, str]:
    """Resolve property type from both description and address evidence."""
    lowered = raw.casefold()
    # Some CNAP extracts leave ``Тип об’єкта`` vague while the full address
    # still contains an explicit apartment/premises marker.  Use both sources.
    if "квартира" in lowered or re.search(r"\bквартира\s+[^,]+$", address, re.I):
        return PropertyType.APARTMENT.value, PropertyType.APARTMENT.value
    if "приміщ" in lowered or re.search(r"\bприміщення\s+[^,]+$", address, re.I):
        return PropertyType.PREMISES.value, PropertyType.PREMISES.value
    return raw or PropertyType.OTHER.value, PropertyType.OTHER.value


def _extract_unit(address: str) -> tuple[str, str, str]:
    """Extract building number, unit type and unit number from a query address."""
    building_match = re.search(r"\bбудинок\s+([^,]+)", address, flags=re.IGNORECASE)
    building_number = _compact(building_match.group(1)) if building_match else ""

    apartment = re.search(r"\bквартира\s+(.+?)\s*$", address, flags=re.IGNORECASE)
    if apartment:
        return building_number, PropertyType.APARTMENT.value, _compact(apartment.group(1))

    premises = re.search(r"\bприміщення\s+(.+?)\s*$", address, flags=re.IGNORECASE)
    if premises:
        return building_number, PropertyType.PREMISES.value, _compact(premises.group(1))

    return building_number, PropertyType.OTHER.value, ""


def _split_property_blocks(lines: list[_Line]) -> list[list[_Line]]:
    """Split the flattened document into property sections by official marker."""
    starts = [index for index, line in enumerate(lines) if line.text == PROPERTY_MARKER]
    blocks: list[list[_Line]] = []
    for pos, start in enumerate(starts):
        end = starts[pos + 1] if pos + 1 < len(starts) else len(lines)
        block = lines[start:end]
        # The extract may append a legacy registry section after current rights.
        # Stop before that marker so similarly worded legacy data cannot be
        # mistaken for current ownership records.
        for index, line in enumerate(block):
            if END_REGISTRY_MARKER in line.text:
                cut = index - 1 if index > 0 and block[index - 1].text == "ВІДОМОСТІ" else index
                block = block[:cut]
                break
        if block:
            blocks.append(block)
    return blocks


def _split_right_blocks(lines: list[_Line]) -> list[list[_Line]]:
    """Split one property section into individual registered-right blocks."""
    starts = [index for index, line in enumerate(lines) if line.text.startswith(RIGHT_MARKER)]
    if not starts:
        return []
    blocks: list[list[_Line]] = []
    for pos, start in enumerate(starts):
        end = starts[pos + 1] if pos + 1 < len(starts) else len(lines)
        blocks.append(lines[start:end])
    return blocks


def _parse_owner(owner_raw: str) -> tuple[str, str, str, str]:
    """Normalize an owner and extract legal-entity metadata when present."""
    owner_raw = _compact(owner_raw)
    code_match = re.search(r",\s*код\s+ЄДРПОУ:\s*(\d+)", owner_raw, flags=re.IGNORECASE)
    country_match = re.search(r",\s*країна\s+реєстрації:\s*(.+)$", owner_raw, flags=re.IGNORECASE)
    if code_match:
        name = owner_raw[: code_match.start()].strip(" ,")
        return (
            name,
            OwnerType.LEGAL_ENTITY.value,
            code_match.group(1),
            _compact(country_match.group(1)) if country_match else "",
        )
    return owner_raw, OwnerType.INDIVIDUAL.value, "", ""


def _parse_ownership(block: list[_Line]) -> OwnershipDraft:
    """Parse one source right block into an immutable ownership draft."""
    text = _flat(block)
    number_match = re.search(r"Номер відомостей про речове право:\s*(\d+)", text, re.I)
    right_record_number = number_match.group(1) if number_match else ""

    right_type = _extract_between(
        text,
        r"Тип речового права:\s*",
        (
            r"Вид спільної власності:",
            r"Розмір частки:",
            r"Власники:",
            r"Відомості про реєстрацію до",
        ),
    )
    joint_ownership_type = _extract_between(
        text,
        r"Вид спільної власності:\s*",
        (r"Розмір частки:", r"Власники:", r"Відомості про реєстрацію до"),
    )
    share_raw = _extract_between(
        text,
        r"Розмір частки:\s*",
        (r"Власники:", r"Відомості про реєстрацію до"),
    )
    numerator, denominator = _parse_share(share_raw)

    owner_raw = _extract_between(
        text,
        r"Власники:\s*",
        (r"Відомості про реєстрацію до",),
    )
    if not owner_raw:
        raise RegistryImportError(
            RegistryImportMessage.OWNER_MISSING.format(
                number=right_record_number or "?",
                page=block[0].page,
            )
        )
    owner_name, owner_type, legal_code, country = _parse_owner(owner_raw)

    # Legacy registration text is retained for traceability even though the
    # current clean owner view does not expose these fields directly.
    legacy_raw = _extract_between(
        text,
        r"Відомості про реєстрацію до\s+поновлення/перенесення:\s*",
        (),
    )
    legacy_registry_name = ""
    legacy_record_number = ""
    legacy_registered_at = ""
    if legacy_raw:
        legacy_match = re.search(
            r"^(.*?),\s*номер запису:\s*(\d+),\s*([0-9.]+\s+[0-9:]+)$",
            legacy_raw,
            flags=re.IGNORECASE,
        )
        if legacy_match:
            legacy_registry_name = _compact(legacy_match.group(1))
            legacy_record_number = legacy_match.group(2)
            legacy_registered_at = legacy_match.group(3)

    return OwnershipDraft(
        right_record_number=right_record_number,
        right_type=right_type,
        joint_ownership_type=joint_ownership_type,
        share_raw=share_raw,
        share_numerator=numerator,
        share_denominator=denominator,
        owner_name_raw=owner_raw,
        owner_name=owner_name,
        owner_type=owner_type,
        legal_entity_code=legal_code,
        registration_country=country,
        legacy_registration_raw=legacy_raw,
        legacy_registry_name=legacy_registry_name,
        legacy_record_number=legacy_record_number,
        legacy_registered_at=legacy_registered_at,
        source_page=block[0].page,
        raw_text=_join(block),
    )


def _parse_property(block: list[_Line]) -> PropertyDraft:
    """Parse one property section and all ownership records attached to it."""
    text = _flat(block)
    registry_match = re.search(
        r"Реєстраційний номер об’єкта\s+нерухомого майна:\s*(\d+)", text, re.I
    )
    registry_number = registry_match.group(1) if registry_match else ""
    if not registry_number:
        raise RegistryImportError(
            RegistryImportMessage.REGISTRY_NUMBER_MISSING.format(page=block[0].page)
        )

    object_description = _extract_between(
        text,
        r"Об’єкт речових прав:\s*",
        (r"Тип об’єкта:", r"Ідентифікатор об’єкта в", r"Площа:"),
    )
    object_type_raw = _extract_between(
        text,
        r"Тип об’єкта:\s*",
        (r"Ідентифікатор об’єкта в", r"Площа:", r"Адреса:"),
    )
    edessb_identifier = _extract_between(
        text,
        r"Ідентифікатор об’єкта в\s+ЄДЕССБ:\s*",
        (r"Площа:", r"Адреса:"),
    )

    area_text = _extract_between(text, r"Площа:\s*", (r"Адреса:",))
    total_match = re.search(r"Загальна площа \(кв\.м\):\s*([0-9]+(?:[.,][0-9]+)?)", area_text, re.I)
    if not total_match:
        raise RegistryImportError(
            RegistryImportMessage.TOTAL_AREA_MISSING.format(
                number=registry_number,
                page=block[0].page,
            )
        )
    total_area = _parse_decimal(total_match.group(1), "загальну площу")
    living_match = re.search(r"житлова площа \(кв\.м\):\s*([0-9]+(?:[.,][0-9]+)?)", area_text, re.I)
    living_area = _parse_decimal(living_match.group(1), "житлову площу") if living_match else None

    address = _extract_between(text, r"Адреса:\s*", (r"Відомості про права власності",))
    if not address:
        raise RegistryImportError(
            RegistryImportMessage.ADDRESS_MISSING.format(number=registry_number)
        )
    building_number, unit_type_from_address, unit_number = _extract_unit(address)
    object_type, normalized_unit_type = _normalize_property_type(object_type_raw, address)
    unit_type = (
        unit_type_from_address
        if unit_type_from_address != PropertyType.OTHER.value
        else normalized_unit_type
    )

    ownership_marker_index = next(
        (i for i, line in enumerate(block) if line.text == "Відомості про права власності"), None
    )
    if ownership_marker_index is None:
        raise RegistryImportError(
            RegistryImportMessage.OWNERSHIP_BLOCK_MISSING.format(number=registry_number)
        )
    ownership_blocks = _split_right_blocks(block[ownership_marker_index + 1 :])
    ownerships = tuple(_parse_ownership(right) for right in ownership_blocks)
    if not ownerships:
        raise RegistryImportError(
            RegistryImportMessage.OWNERS_MISSING.format(number=registry_number)
        )

    return PropertyDraft(
        registry_number=registry_number,
        object_description=object_description,
        object_type_raw=object_type_raw,
        object_type=object_type,
        edessb_identifier=edessb_identifier,
        total_area=total_area,
        living_area=living_area,
        address_raw=address,
        building_number=building_number,
        unit_type=unit_type,
        unit_number=unit_number,
        source_page_start=block[0].page,
        source_page_end=block[-1].page,
        raw_text=_join(block),
        ownerships=ownerships,
    )


def _header_value(text: str, pattern: str, end_patterns: tuple[str, ...]) -> str:
    """Read one informational-header field using the shared marker strategy."""
    return _extract_between(text, pattern, end_patterns)


class CnapPdfImporter:
    """Parse CNAP property-registry extracts into a validated domain draft.

    The source PDF is not a semantic table: PyMuPDF exposes visually arranged
    text lines.  Parsing therefore relies on stable official textual markers,
    preserves page/raw text for diagnostics, and validates ownership invariants
    before any data reaches SQLite.
    """

    def parse(self, path: Path) -> RegistryDocumentDraft:
        """Parse a supported PDF completely or raise ``RegistryImportError``."""
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(path)

        # Hash the original file, not extracted text: the repository uses this
        # as a stable identity to prevent importing the exact same source twice.
        source_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        try:
            document = pymupdf.open(path)
        except Exception as exc:
            raise RegistryImportError(
                RegistryImportMessage.PDF_OPEN_FAILED.format(error=exc)
            ) from exc

        try:
            pages: list[RegistryPageDraft] = []
            lines: list[_Line] = []
            for page_number, page in enumerate(document, start=1):
                # Preserve the full text page before filtering parser noise.
                # This gives future diagnostics access to the original extraction.
                page_text = page.get_text("text")
                pages.append(RegistryPageDraft(page_number, page_text))
                for raw_line in page_text.splitlines():
                    line = raw_line.strip()
                    if not line or re.fullmatch(r"стор\.\s*\d+\s+з\s+\d+", line, re.I):
                        continue
                    # Generated page footers and RRP document ids are layout
                    # noise; keeping them would interfere with marker adjacency.
                    if re.fullmatch(r"RRP-[A-Z0-9]+", line):
                        continue
                    lines.append(_Line(page_number, line))
        finally:
            document.close()

        first_property = next(
            (i for i, line in enumerate(lines) if line.text == PROPERTY_MARKER),
            None,
        )
        if first_property is None:
            raise RegistryImportError(RegistryImportMessage.UNSUPPORTED_DOCUMENT)

        header = _flat(lines[:first_property])
        info_number = _header_value(
            header,
            r"Номер інформаційної довідки:\s*",
            (r"Дата, час формування:",),
        )
        formed_at = _header_value(
            header,
            r"Дата, час формування:\s*",
            (r"Інформаційну довідку\s+сформовано:",),
        )
        formed_by = _header_value(
            header,
            r"Інформаційну довідку\s+сформовано:\s*",
            (r"Підстава формування\s+інформаційної довідки:",),
        )
        formation_basis = _header_value(
            header,
            r"Підстава формування\s+інформаційної довідки:\s*",
            (r"Параметри запиту",),
        )
        query_type = _header_value(
            header,
            r"Пошук в Державному реєстрі\s+речових прав на нерухоме\s+майно про:\s*",
            (r"Адреса / Місцезнаходження:",),
        )
        query_address = _header_value(
            header,
            r"Адреса / Місцезнаходження:\s*",
            (r"ВІДОМОСТІ",),
        )

        properties = tuple(_parse_property(block) for block in _split_property_blocks(lines))
        if not properties:
            raise RegistryImportError(RegistryImportMessage.PROPERTIES_MISSING)

        self._validate(properties)
        return RegistryDocumentDraft(
            source_filename=path.name,
            source_sha256=source_sha256,
            page_count=len(pages),
            information_reference_number=info_number,
            formed_at=formed_at,
            formed_by=formed_by,
            formation_basis=formation_basis,
            query_type=query_type,
            query_address=query_address,
            pages=tuple(pages),
            properties=properties,
        )

    @staticmethod
    def _validate(properties: tuple[PropertyDraft, ...]) -> None:
        """Validate document-level uniqueness and complete ownership shares."""
        registry_numbers: set[str] = set()
        for prop in properties:
            if prop.registry_number in registry_numbers:
                raise RegistryImportError(
                    RegistryImportMessage.DUPLICATE_PROPERTY.format(number=prop.registry_number)
                )
            registry_numbers.add(prop.registry_number)

            effective: list[Fraction] = []
            for ownership in prop.ownerships:
                explicit = ownership.explicit_share
                if explicit is None:
                    # CNAP may omit the share for a sole owner; legally/effectively
                    # that row represents the full property.  With multiple owners
                    # omission is ambiguous and must be rejected instead of guessed.
                    if len(prop.ownerships) == 1:
                        effective.append(Fraction(1, 1))
                    else:
                        raise RegistryImportError(
                            RegistryImportMessage.SHARES_MISSING.format(
                                number=prop.registry_number
                            )
                        )
                else:
                    effective.append(explicit)
            if sum(effective, Fraction(0, 1)) != Fraction(1, 1):
                raise RegistryImportError(
                    RegistryImportMessage.SHARES_SUM_INVALID.format(
                        number=prop.registry_number,
                        value=sum(effective, Fraction(0, 1)),
                    )
                )
