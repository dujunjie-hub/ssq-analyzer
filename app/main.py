from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SSQ Analyzer desktop app")
    parser.add_argument("--check", action="store_true", help="validate app imports without opening the GUI")
    args = parser.parse_args(argv)

    if args.check:
        from app.scripts.registry import create_default_registry

        create_default_registry()
        return 0

    try:
        from PySide6.QtWidgets import QApplication
    except ModuleNotFoundError:
        print("缺少 PySide6。请先运行：python3 -m pip install -r requirements.txt", file=sys.stderr)
        return 2

    from app.gui.main_window import MainWindow

    qt_app = QApplication(sys.argv[:1])
    window = MainWindow()
    window.resize(1180, 760)
    window.show()
    return qt_app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

