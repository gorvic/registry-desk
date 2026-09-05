from pathlib import Path
import ast
import re


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "registrydesk"


def _python_files(root: Path):
    return root.rglob("*.py")


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module)
    return result


def test_dependency_direction_is_preserved() -> None:
    forbidden_gui = (
        "registrydesk.repositories",
        "registrydesk.services",
        "registrydesk.storage",
        "registrydesk.presentation",
    )
    for path in _python_files(PACKAGE / "interfaces"):
        imports = _imports(path)
        assert not any(item.startswith(forbidden_gui) for item in imports), path

    forbidden_application = (
        "registrydesk.repositories",
        "registrydesk.storage",
        "registrydesk.presentation",
    )
    for path in _python_files(PACKAGE / "application"):
        imports = _imports(path)
        assert not any(item.startswith(forbidden_application) for item in imports), path


def test_pickle_support_is_removed() -> None:
    for path in _python_files(PACKAGE):
        text = path.read_text(encoding="utf-8").casefold()
        assert "pickle" not in text, path


def test_gui_geometry_literals_are_centralized() -> None:
    geometry = PACKAGE / "interfaces" / "gui" / "geometry.py"
    for path in _python_files(PACKAGE / "interfaces" / "gui"):
        if path == geometry:
            continue
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"\bresize\(\s*\d", text), path
        assert not re.search(r"\bsetMinimumSize\(\s*\d", text), path
        assert not re.search(r"\bsetColumnWidth\([^,]+,\s*\d", text), path
        assert not re.search(r"\bsetFixedWidth\(\s*\d", text), path


def test_modern_python_structure_has_no_hidden_composition() -> None:
    mixins: list[str] = []
    multiple_inheritance: list[str] = []
    postponed: list[str] = []
    type_ignores: list[str] = []

    for path in _python_files(PACKAGE):
        text = path.read_text(encoding="utf-8")
        if "from __future__ import annotations" in text:
            postponed.append(str(path))
        if "type: ignore" in text:
            type_ignores.append(str(path))
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name.endswith("Mixin"):
                    mixins.append(f"{path}:{node.name}")
                if len(node.bases) > 1:
                    multiple_inheritance.append(f"{path}:{node.name}")

    assert not mixins
    assert not multiple_inheritance
    assert not postponed
    assert not type_ignores


def test_public_source_documentation_contract_is_preserved() -> None:
    """Public source should stay self-describing as the project evolves."""
    missing: list[str] = []

    for path in _python_files(PACKAGE):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if not ast.get_docstring(tree):
            missing.append(f"{path}: module")

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and not ast.get_docstring(node):
                missing.append(f"{path}:{node.lineno}: class {node.name}")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_") and not ast.get_docstring(node):
                    missing.append(f"{path}:{node.lineno}: function {node.name}")

    assert not missing, "\n".join(missing)
