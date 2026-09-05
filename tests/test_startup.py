from pathlib import Path
import os
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def _env() -> dict[str, str]:
    env = dict(os.environ)
    current = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(SRC) if not current else f"{SRC}{os.pathsep}{current}"
    return env


def test_bootstrap_import_does_not_load_optional_document_stacks() -> None:
    script = """
import sys
import registrydesk.bootstrap
heavy = ('pymupdf', 'openpyxl', 'reportlab')
loaded = [name for name in heavy if any(m == name or m.startswith(name + '.') for m in sys.modules)]
sys.exit(','.join(loaded)) if loaded else None
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env=_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
