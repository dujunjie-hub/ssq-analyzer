from __future__ import annotations

import csv
import re
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

from ssq_analyzer.models import Draw


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_HISTORY_PATH = DATA_DIR / "ssq_history.csv"
DEFAULT_FETCH_URL = "https://datachart.500.com/ssq/history/newinc/history.php?start=1&end=99999"


class DataFetchError(RuntimeError):
    """Raised when remote history data cannot be downloaded or parsed."""


SAMPLE_DRAWS = [
    Draw("2026001", date(2026, 1, 1), (1, 5, 8, 12, 19, 26), 6),
    Draw("2026002", date(2026, 1, 3), (3, 7, 11, 16, 22, 30), 12),
    Draw("2026003", date(2026, 1, 5), (2, 9, 14, 18, 25, 33), 4),
    Draw("2026004", date(2026, 1, 7), (6, 10, 13, 21, 27, 31), 9),
    Draw("2026005", date(2026, 1, 10), (4, 15, 17, 20, 24, 29), 15),
    Draw("2026006", date(2026, 1, 12), (1, 8, 12, 23, 28, 32), 2),
]


def load_draws(path: Path = DEFAULT_HISTORY_PATH) -> list[Draw]:
    if not path.exists():
        return list(SAMPLE_DRAWS)

    draws: list[Draw] = []
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            draws.append(
                Draw(
                    issue=row["issue"],
                    draw_date=date.fromisoformat(row["date"]),
                    red=tuple(int(row[f"red_{index}"]) for index in range(1, 7)),
                    blue=int(row["blue"]),
                )
            )
    return sorted(draws, key=lambda draw: draw.issue)


def save_draws(draws: list[Draw], path: Path = DEFAULT_HISTORY_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["issue", "date", "red_1", "red_2", "red_3", "red_4", "red_5", "red_6", "blue"],
        )
        writer.writeheader()
        for draw in sorted(draws, key=lambda item: item.issue):
            writer.writerow(
                {
                    "issue": draw.issue,
                    "date": draw.draw_date.isoformat(),
                    "red_1": draw.red[0],
                    "red_2": draw.red[1],
                    "red_3": draw.red[2],
                    "red_4": draw.red[3],
                    "red_5": draw.red[4],
                    "red_6": draw.red[5],
                    "blue": draw.blue,
                }
            )
    return path


def fetch_draws(url: str = DEFAULT_FETCH_URL) -> list[Draw]:
    request = urllib.request.Request(url, headers={"User-Agent": "ssq-analyzer/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            html = response.read().decode("gb2312", errors="ignore")
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        reason = getattr(error, "reason", error)
        raise DataFetchError(f"无法访问开奖数据源：{reason}") from error

    draws = parse_500_history_html(html)
    if not draws:
        raise DataFetchError("开奖数据源未返回有效历史数据")
    return draws


def parse_500_history_html(html: str) -> list[Draw]:
    rows = re.findall(r"<tr[^>]*?>(.*?)</tr>", html, flags=re.S | re.I)
    draws: list[Draw] = []
    for row in rows:
        cells = [re.sub(r"<.*?>", "", cell).strip() for cell in re.findall(r"<td[^>]*?>(.*?)</td>", row, re.S | re.I)]
        if len(cells) < 15 or not cells[0].isdigit():
            continue
        parsed = _parse_draw_cells(cells)
        if parsed is None:
            continue
        issue, balls = parsed
        draw_date = _parse_date(cells[-1])
        if draw_date is None:
            continue
        draws.append(Draw(issue=issue, draw_date=draw_date, red=tuple(sorted(balls[:6])), blue=balls[6]))
    return sorted(draws, key=lambda draw: draw.issue)


def _parse_draw_cells(cells: list[str]) -> tuple[str, list[int]] | None:
    for issue_index in (0, 1):
        if issue_index >= len(cells):
            continue
        issue = cells[issue_index]
        if not issue.isdigit() or len(issue) < 5:
            continue
        ball_cells = cells[issue_index + 1 : issue_index + 8]
        if len(ball_cells) != 7 or not all(value.isdigit() for value in ball_cells):
            continue
        balls = [int(value) for value in ball_cells]
        red = balls[:6]
        blue = balls[6]
        if all(1 <= ball <= 33 for ball in red) and 1 <= blue <= 16:
            return issue, balls
    return None


def _parse_date(value: str) -> date | None:
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", value)
    if not match:
        return None
    return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
