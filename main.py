"""Development launcher for the src-layout project."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from registrydesk.runtime import run  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(run())
