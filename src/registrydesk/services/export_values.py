"""Shared value formatting for non-formula export formats."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction

from registrydesk.domain.registry import RegistryRow

SMART_DECIMAL_PLACES = 12


def owner_display_name(row: RegistryRow) -> str:
    if row.owner_type != "юридична особа":
        return row.owner_name
    suffix: list[str] = []
    if row.legal_entity_code:
        suffix.append(f"код ЄДРПОУ: {row.legal_entity_code}")
    if row.registration_country:
        suffix.append(f"країна реєстрації: {row.registration_country}")
    return f"{row.owner_name}, {', '.join(suffix)}" if suffix else row.owner_name


def fraction_decimal(value: Fraction) -> Decimal:
    return Decimal(value.numerator) / Decimal(value.denominator)


def fixed_two(value: Decimal | Fraction) -> str:
    decimal_value = fraction_decimal(value) if isinstance(value, Fraction) else value
    rounded = decimal_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{rounded:.2f}"


def smart_decimal(value: Decimal | Fraction, max_places: int = SMART_DECIMAL_PLACES) -> str:
    decimal_value = fraction_decimal(value) if isinstance(value, Fraction) else value
    quantum = Decimal(1).scaleb(-max_places)
    rounded = decimal_value.quantize(quantum, rounding=ROUND_HALF_UP)
    text = format(rounded, "f").rstrip("0").rstrip(".")
    return text or "0"


def plain_export_value(key: str, row: RegistryRow, sequence: int) -> str:
    """Return a lossless/readable textual value for CSV and PDF exports."""
    if key == "unit_number":
        return row.unit_number
    if key == "property_type":
        return row.property_type
    if key == "owner_no":
        return str(sequence)
    if key == "owner_name":
        return owner_display_name(row)
    if key == "share":
        return smart_decimal(row.share)
    if key == "ownership_area":
        return smart_decimal(row.ownership_area)
    if key == "total_area":
        return smart_decimal(row.total_area)
    if key == "living_area":
        return smart_decimal(row.living_area) if row.living_area is not None else ""
    if key == "registry_number":
        return row.registry_number
    if key == "right_record_numbers":
        return ", ".join(row.right_record_numbers)
    if key == "right_type":
        return row.right_type
    if key == "joint_ownership_type":
        return row.joint_ownership_type
    if key == "edessb_identifier":
        return row.edessb_identifier
    if key == "address":
        return row.address
    if key == "owner_type":
        return row.owner_type
    if key == "legal_entity_code":
        return row.legal_entity_code
    if key == "registration_country":
        return row.registration_country
    raise KeyError(key)


def pdf_export_value(key: str, row: RegistryRow, sequence: int) -> str:
    """Return PDF display text with exact shares and two-decimal areas."""
    if key == "share":
        return row.share_text
    if key == "ownership_area":
        return fixed_two(row.ownership_area)
    if key == "total_area":
        return fixed_two(row.total_area)
    return plain_export_value(key, row, sequence)
