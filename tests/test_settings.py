from pathlib import Path

from registrydesk.config.settings import AppSettings
from registrydesk.config.theme import Theme


def test_theme_defaults_to_system(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("THEME", raising=False)
    assert AppSettings.load(tmp_path).theme is Theme.SYSTEM


def test_theme_is_loaded_once_from_env_file(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("THEME", raising=False)
    (tmp_path / ".env").write_text("THEME=dark\n", encoding="utf-8")
    assert AppSettings.load(tmp_path).theme is Theme.DARK


def test_unknown_theme_falls_back_to_system(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("THEME", "unknown")
    assert AppSettings.load(tmp_path).theme is Theme.SYSTEM


def test_theme_contract_has_exactly_three_startup_values() -> None:
    assert tuple(item.value for item in Theme) == ("system", "light", "dark")
