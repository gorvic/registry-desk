from registrydesk.common.sorting import (
    natural_text_key,
    property_unit_sort_key,
    ukrainian_text_key,
)


def test_natural_text_key_sorts_unit_numbers_numerically():
    values = ["1", "10", "100", "101", "11", "2", "192-4", "192-2", "192-10"]
    assert sorted(values, key=natural_text_key) == [
        "1",
        "2",
        "10",
        "11",
        "100",
        "101",
        "192-2",
        "192-4",
        "192-10",
    ]


def test_ukrainian_text_key_respects_i_and_yi_order():
    values = ["Їжак", "Іван", "Зоря", "Ирина"]
    assert sorted(values, key=ukrainian_text_key) == ["Зоря", "Ирина", "Іван", "Їжак"]


def test_property_unit_sort_key_prioritizes_apartments_then_natural_number():
    values = [
        ("приміщення", "2"),
        ("квартира", "100"),
        ("квартира", "10"),
        ("приміщення", "1"),
        ("квартира", "1"),
        ("приміщення", "192-2"),
    ]
    assert sorted(values, key=lambda item: property_unit_sort_key(*item)) == [
        ("квартира", "1"),
        ("квартира", "10"),
        ("квартира", "100"),
        ("приміщення", "1"),
        ("приміщення", "2"),
        ("приміщення", "192-2"),
    ]


def test_descending_property_key_keeps_apartments_first_when_qt_reverses_order():
    values = [
        ("приміщення", "2"),
        ("квартира", "100"),
        ("квартира", "10"),
        ("приміщення", "1"),
        ("квартира", "1"),
        ("приміщення", "192-2"),
    ]
    ascending_keys = sorted(
        values,
        key=lambda item: property_unit_sort_key(*item, descending=True),
        reverse=True,
    )
    assert ascending_keys == [
        ("квартира", "100"),
        ("квартира", "10"),
        ("квартира", "1"),
        ("приміщення", "192-2"),
        ("приміщення", "2"),
        ("приміщення", "1"),
    ]
