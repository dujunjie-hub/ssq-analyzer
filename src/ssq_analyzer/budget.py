from __future__ import annotations

from dataclasses import dataclass
from math import comb


TICKET_PRICE = 2
FIRST_PRIZE_COMBINATIONS = comb(33, 6) * 16


@dataclass(frozen=True)
class BudgetPlan:
    mode: str
    budget: int
    combination_count: int
    cost: int
    red_count: int
    blue_count: int
    red_dan_count: int = 0
    red_tuo_count: int = 0

    @property
    def remaining_budget(self) -> int:
        return self.budget - self.cost

    @property
    def first_prize_denominator(self) -> int:
        return FIRST_PRIZE_COMBINATIONS

    @property
    def first_prize_probability(self) -> float:
        return self.combination_count / FIRST_PRIZE_COMBINATIONS


def calculate_budget_plan(mode: str, budget: int, red_dan_count: int = 1) -> BudgetPlan:
    if mode not in {"compound", "dantuo"}:
        raise ValueError("mode must be compound or dantuo")
    if budget < 0:
        raise ValueError("budget must not be negative")
    if mode == "compound":
        lines, red_count, blue_count = _best_compound(budget)
        return BudgetPlan(mode, budget, lines, lines * TICKET_PRICE, red_count, blue_count)
    if not 1 <= red_dan_count <= 5:
        raise ValueError("red_dan_count must be between 1 and 5")
    lines, red_tuo_count, blue_count = _best_dantuo(budget, red_dan_count)
    return BudgetPlan(
        mode,
        budget,
        lines,
        lines * TICKET_PRICE,
        red_dan_count + red_tuo_count if lines else 0,
        blue_count,
        red_dan_count if lines else 0,
        red_tuo_count,
    )


def _best_compound(budget: int) -> tuple[int, int, int]:
    best = (0, 0, 0)
    for red_count in range(6, 34):
        for blue_count in range(1, 17):
            lines = comb(red_count, 6) * blue_count
            if lines * TICKET_PRICE <= budget:
                best = max(best, (lines, red_count, blue_count))
    return best


def _best_dantuo(budget: int, red_dan_count: int) -> tuple[int, int, int]:
    best = (0, 0, 0)
    need_tuo = 6 - red_dan_count
    for red_tuo_count in range(need_tuo, 34 - red_dan_count):
        for blue_count in range(1, 17):
            lines = comb(red_tuo_count, need_tuo) * blue_count
            if lines * TICKET_PRICE <= budget:
                best = max(best, (lines, red_tuo_count, blue_count))
    return best
