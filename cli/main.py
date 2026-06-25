from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ssq_analyzer.cli import main as _main


def main(argv: list[str] | None = None) -> int:
    return _main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
