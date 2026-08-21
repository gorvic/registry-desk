"""Human-friendly sort keys used by GUI views."""

from __future__ import annotations

import re

_UKRAINIAN_ALPHABET = "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
_UKRAINIAN_ORDER = {char: index + 100 for index, char in enumerate(_UKRAINIAN_ALPHABET)}
_PROPERTY_TYPE_ORDER = {"квартира": 0, "приміщення": 1}


def ukrainian_text_key(value: str) -> tuple[int, ...]:
    """Return a deterministic Ukrainian-alphabet key for case-insensitive text sorting."""
    result: list[int] = []
    for char in value.casefold():
        if char.isspace():
            result.append(0)
        elif char in _UKRAINIAN_ORDER:
            result.append(_UKRAINIAN_ORDER[char])
        else:
            result.append(1000 + ord(char))
    return tuple(result)


def natural_text_key(value: str) -> tuple[tuple[int, object], ...]:
    """Sort embedded digit runs numerically: 1, 2, 10, 11, 100, 192-1, 192-2."""
    parts = re.findall(r"\d+|\D+", value.casefold())
    return tuple(
        (0, int(part)) if part.isdigit() else (1, ukrainian_text_key(part))
        for part in parts
    )


def property_unit_sort_key(
    property_type: str,
    unit_number: str,
    *,
    descending: bool = False,
) -> tuple[int, tuple[tuple[int, object], ...], tuple[int, ...]]:
    """Sort apartments before premises, then sort their numbers naturally.

    Qt reverses the whole comparison for descending order. Negating only the type
    rank keeps apartments ahead of premises while the unit number itself reverses.
    """
    type_rank = _PROPERTY_TYPE_ORDER.get(property_type, 2)
    type_key = -type_rank if descending else type_rank
    return (
        type_key,
        natural_text_key(unit_number),
        ukrainian_text_key(property_type),
    )
