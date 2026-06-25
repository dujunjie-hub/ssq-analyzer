from __future__ import annotations

import csv
import json
from pathlib import Path

from app.core.analyzer_service import AnalyzerResult


def format_result_text(result: AnalyzerResult) -> str:
    parts = [result.title]
    if result.logs:
        parts.append("执行日志：")
        parts.extend(result.logs)
    if result.summary_text:
        parts.append("结果：")
        parts.append(result.summary_text)
    return "\n".join(str(part) for part in parts if str(part))


def export_result(result: AnalyzerResult, path: Path | str) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    suffix = output.suffix.lower()
    if suffix == ".json":
        _write_json(result, output)
    elif suffix == ".txt":
        output.write_text(format_result_text(result), encoding="utf-8")
    else:
        _write_csv(result.rows, output)
    return output


def _write_json(result: AnalyzerResult, path: Path) -> None:
    payload = {
        "command": result.command,
        "title": result.title,
        "logs": result.logs,
        "summary_text": result.summary_text,
        "metadata": result.metadata,
        "rows": result.rows,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_csv(rows: list[dict[str, object]], path: Path) -> None:
    fieldnames = _fieldnames(rows)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _fieldnames(rows: list[dict[str, object]]) -> list[str]:
    if not rows:
        return ["message"]
    return list(rows[0].keys())

