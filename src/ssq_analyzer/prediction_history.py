from __future__ import annotations

import json
import os
from pathlib import Path

from ssq_analyzer.models import Ticket


def prediction_history_path() -> Path:
    override = os.environ.get("SSQ_PREDICTION_HISTORY_PATH")
    if override:
        return Path(override)
    return Path.home() / "Library" / "Application Support" / "SSQ Analyzer" / "prediction_history.json"


def load_prediction(source_issue: str, path: Path | None = None) -> list[Ticket] | None:
    try:
        with (path or prediction_history_path()).open("r", encoding="utf-8") as file:
            record = json.load(file).get(str(source_issue), {})
        return [Ticket(tuple(int(ball) for ball in ticket["red"]), int(ticket["blue"])) for ticket in record["tickets"]]
    except (FileNotFoundError, OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def save_prediction(
    source_issue: str,
    tickets: list[Ticket],
    strategy: str,
    seed: int | None,
    path: Path | None = None,
) -> bool:
    output = path or prediction_history_path()
    try:
        history = _load_history(output)
        history[str(source_issue)] = {
            "strategy": strategy,
            "seed": seed,
            "tickets": [{"red": list(ticket.red), "blue": ticket.blue} for ticket in tickets],
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_name(f"{output.name}.tmp")
        temporary.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(output)
        return True
    except OSError:
        return False


def _load_history(path: Path) -> dict[str, object]:
    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        return payload if isinstance(payload, dict) else {}
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}
