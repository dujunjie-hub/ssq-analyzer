from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from ssq_analyzer.models import BLUE_RANGE, RED_RANGE, Draw


@dataclass(frozen=True)
class AnalysisResult:
    red_frequency: dict[int, int]
    blue_frequency: dict[int, int]
    red_omissions: dict[int, int]
    blue_omissions: dict[int, int]
    parity_counts: dict[str, int]
    range_counts: dict[str, dict[str, int]]
    consecutive_counts: dict[int, int]


def analyze_draws(draws: list[Draw]) -> AnalysisResult:
    ordered = sorted(draws, key=lambda draw: draw.issue)
    red_frequency = {ball: 0 for ball in RED_RANGE}
    blue_frequency = {ball: 0 for ball in BLUE_RANGE}
    parity_counter: Counter[str] = Counter()
    range_counter: Counter[str] = Counter()
    consecutive_counter: Counter[int] = Counter()

    for draw in ordered:
        for ball in draw.red:
            red_frequency[ball] += 1
        blue_frequency[draw.blue] += 1
        parity_counter[_parity_key(draw.red)] += 1
        range_counter[_range_key(draw.red)] += 1
        consecutive_counter[_consecutive_pairs(draw.red)] += 1

    return AnalysisResult(
        red_frequency=red_frequency,
        blue_frequency=blue_frequency,
        red_omissions=red_omissions(ordered),
        blue_omissions=blue_omissions(ordered),
        parity_counts=dict(parity_counter),
        range_counts={"low_mid_high": dict(range_counter)},
        consecutive_counts=dict(consecutive_counter),
    )


def red_omissions(draws: list[Draw]) -> dict[int, int]:
    return _omissions(draws, RED_RANGE, lambda draw: draw.red)


def blue_omissions(draws: list[Draw]) -> dict[int, int]:
    return _omissions(draws, BLUE_RANGE, lambda draw: (draw.blue,))


def analysis_rows(result: AnalysisResult) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for ball in RED_RANGE:
        rows.append(
            {
                "type": "red",
                "ball": ball,
                "frequency": result.red_frequency[ball],
                "omission": result.red_omissions[ball],
            }
        )
    for ball in BLUE_RANGE:
        rows.append(
            {
                "type": "blue",
                "ball": ball,
                "frequency": result.blue_frequency[ball],
                "omission": result.blue_omissions[ball],
            }
        )
    return rows


def _omissions(draws: list[Draw], ball_range: range, pick_balls) -> dict[int, int]:
    ordered = sorted(draws, key=lambda draw: draw.issue)
    result: dict[int, int] = {}
    for ball in ball_range:
        omission = len(ordered)
        for distance, draw in enumerate(reversed(ordered)):
            if ball in pick_balls(draw):
                omission = distance
                break
        result[ball] = omission
    return result


def _parity_key(red: tuple[int, ...]) -> str:
    odd = sum(1 for ball in red if ball % 2)
    even = len(red) - odd
    return f"{odd}:{even}"


def _range_key(red: tuple[int, ...]) -> str:
    low = sum(1 for ball in red if 1 <= ball <= 11)
    mid = sum(1 for ball in red if 12 <= ball <= 22)
    high = sum(1 for ball in red if 23 <= ball <= 33)
    return f"{low}:{mid}:{high}"


def _consecutive_pairs(red: tuple[int, ...]) -> int:
    return sum(1 for left, right in zip(red, red[1:]) if right == left + 1)
