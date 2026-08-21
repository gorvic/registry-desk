from __future__ import annotations

from pathlib import Path

from registrydesk.services.pdf_importer import CnapPdfImporter


PDF_TEXT = """RRP-TEST
Інформація з Державного реєстру речових прав
(Щодо багатоквартирного будинку)
Номер інформаційної довідки:
123456
Дата, час формування:
21.08.2026 12:00:00
Інформаційну довідку
сформовано:
Тестова Особа, ЦНАП
Підстава формування
інформаційної довідки:
Заява
Параметри запиту
Пошук в Державному реєстрі
речових прав на нерухоме
майно про:
права власності
Адреса / Місцезнаходження:
м.Київ, вулиця Тестова, будинок 1
ВІДОМОСТІ
З ДЕРЖАВНОГО РЕЄСТРУ РЕЧОВИХ ПРАВ
Актуальна інформація про об’єкт речових прав
Реєстраційний номер об’єкта
нерухомого майна:
10001
Тип об’єкта:
квартира
Площа:
Загальна площа (кв.м): 60.0, житлова площа (кв.м): 30.0
Адреса:
м.Київ, вулиця Тестова, будинок 1, квартира 7
Відомості про права власності
Номер відомостей про речове право: 501
Тип речового права:
право власності
Вид спільної власності:
спільна часткова
Розмір частки:
1/3
Власники:
Іваненко Іван Іванович
Номер відомостей про речове право: 502
Тип речового права:
право власності
Вид спільної власності:
спільна часткова
Розмір частки:
2/3
Власники:
Петренко Петро Петрович
"""


class FakePage:
    def get_text(self, _kind: str) -> str:
        return PDF_TEXT


class FakeDocument:
    def __iter__(self):
        yield FakePage()

    def __len__(self):
        return 1

    def close(self) -> None:
        pass


def test_importer_parses_supported_registry(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "test.pdf"
    source.write_bytes(b"fake")
    monkeypatch.setattr("registrydesk.services.pdf_importer.pymupdf.open", lambda _path: FakeDocument())

    result = CnapPdfImporter().parse(source)

    assert result.information_reference_number == "123456"
    assert result.query_address.endswith("будинок 1")
    assert len(result.properties) == 1
    prop = result.properties[0]
    assert prop.unit_number == "7"
    assert str(prop.total_area) == "60.0"
    assert [item.share_raw for item in prop.ownerships] == ["1/3", "2/3"]
