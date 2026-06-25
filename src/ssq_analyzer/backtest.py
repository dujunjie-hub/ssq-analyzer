from __future__ import annotations

from dataclasses import dataclass

from ssq_analyzer.generator import DEFAULT_TICKET_COUNT, TRANSPARENT_STRATEGIES, generate_tickets
from ssq_analyzer.models import Draw, Ticket


@dataclass(frozen=True)
class TicketResult:
    ticket: Ticket
    red_hits: int
    blue_hit: bool
    tier: str


@dataclass(frozen=True)
class BacktestResult:
    issue: str
    draw_date: str
    actual: Ticket
    generated_tickets: list[TicketResult]
    training_draw_count: int


def prize_tier(red_hits: int, blue_hit: bool) -> str:
    if red_hits == 6 and blue_hit:
        return "first"
    if red_hits == 6:
        return "second"
    if red_hits == 5 and blue_hit:
        return "third"
    if red_hits == 5 or (red_hits == 4 and blue_hit):
        return "fourth"
    if red_hits == 4 or (red_hits == 3 and blue_hit):
        return "fifth"
    if blue_hit:
        return "sixth"
    return "none"


def compare_ticket(ticket: Ticket, actual: Ticket) -> TicketResult:
    red_hits = len(set(ticket.red) & set(actual.red))
    blue_hit = ticket.blue == actual.blue
    return TicketResult(ticket=ticket, red_hits=red_hits, blue_hit=blue_hit, tier=prize_tier(red_hits, blue_hit))


def run_backtest(
    draws: list[Draw],
    strategy: str = "balanced",
    count: int = DEFAULT_TICKET_COUNT,
    seed: int | None = None,
    window: int = 20,
) -> list[BacktestResult]:
    ordered = sorted(draws, key=lambda draw: draw.issue)
    if len(ordered) < 2:
        return []

    start_index = max(1, len(ordered) - window)
    results: list[BacktestResult] = []
    for index in range(start_index, len(ordered)):
        target = ordered[index]
        training = ordered[:index]
        target_seed = None if seed is None else seed + index
        tickets = generate_tickets(training, strategy=strategy, count=count, seed=target_seed)
        ticket_results = [compare_ticket(ticket, target.ticket) for ticket in tickets]
        results.append(
            BacktestResult(
                issue=target.issue,
                draw_date=target.draw_date.isoformat(),
                actual=target.ticket,
                generated_tickets=ticket_results,
                training_draw_count=len(training),
            )
        )
    return results


def backtest_rows(results: list[BacktestResult], strategy: str = "") -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for result in results:
        for index, ticket_result in enumerate(result.generated_tickets, start=1):
            rows.append(
                {
                    "strategy": strategy,
                    "issue": result.issue,
                    "date": result.draw_date,
                    "ticket_index": index,
                    "ticket_red": ticket_result.ticket.red_text(),
                    "ticket_blue": ticket_result.ticket.blue_text(),
                    "actual_red": result.actual.red_text(),
                    "actual_blue": result.actual.blue_text(),
                    "red_hits": ticket_result.red_hits,
                    "blue_hit": "yes" if ticket_result.blue_hit else "no",
                    "tier": ticket_result.tier,
                    "training_draw_count": result.training_draw_count,
                }
            )
    return rows


def summarize_backtest(results: list[BacktestResult], strategy: str) -> dict[str, object]:
    summary: dict[str, object] = {
        "strategy": strategy,
        "draw_count": len(results),
        "total_tickets": 0,
        "blue_hits": 0,
        "blue_hit_rate": "0.000",
    }
    for tier in ["first", "second", "third", "fourth", "fifth", "sixth", "none"]:
        summary[f"tier_{tier}"] = 0
    for hits in range(7):
        summary[f"red_hits_{hits}"] = 0

    total_tickets = 0
    blue_hits = 0
    for result in results:
        for ticket_result in result.generated_tickets:
            total_tickets += 1
            if ticket_result.blue_hit:
                blue_hits += 1
            summary[f"tier_{ticket_result.tier}"] = int(summary[f"tier_{ticket_result.tier}"]) + 1
            summary[f"red_hits_{ticket_result.red_hits}"] = int(summary[f"red_hits_{ticket_result.red_hits}"]) + 1

    summary["total_tickets"] = total_tickets
    summary["blue_hits"] = blue_hits
    summary["blue_hit_rate"] = f"{(blue_hits / total_tickets if total_tickets else 0):.3f}"
    return summary


def compare_strategies(
    draws: list[Draw],
    strategies: list[str] | None = None,
    count: int = DEFAULT_TICKET_COUNT,
    seed: int | None = None,
    window: int = 20,
) -> list[dict[str, object]]:
    selected = strategies or sorted(TRANSPARENT_STRATEGIES)
    summaries: list[dict[str, object]] = []
    for index, strategy in enumerate(selected):
        strategy_seed = None if seed is None else seed + index * 10_000
        results = run_backtest(draws, strategy=strategy, count=count, seed=strategy_seed, window=window)
        summaries.append(summarize_backtest(results, strategy=strategy))
    return summaries
