from __future__ import annotations

import random
from collections.abc import Sequence

from ssq_analyzer.deep_learning import ExperimentalNeuralScorer
from ssq_analyzer.liuyao import LiuyaoReading, cast_liuyao
from ssq_analyzer.models import BLUE_RANGE, RED_RANGE, Draw, Ticket
from ssq_analyzer.stats import analyze_draws


DEFAULT_TICKET_COUNT = 5
TRANSPARENT_STRATEGIES = {"random", "weighted", "balanced", "hot", "cold", "omission", "recent", "ensemble"}
EXPERIMENTAL_STRATEGIES = {"deep-learning"}
MYSTIC_STRATEGIES = {"liuyao"}
STRATEGIES = TRANSPARENT_STRATEGIES | EXPERIMENTAL_STRATEGIES | MYSTIC_STRATEGIES


def generate_tickets(
    history: Sequence[Draw],
    strategy: str = "balanced",
    count: int = DEFAULT_TICKET_COUNT,
    seed: int | None = None,
) -> list[Ticket]:
    if strategy not in STRATEGIES:
        raise ValueError(f"strategy must be one of {', '.join(sorted(STRATEGIES))}")
    if count < 1:
        raise ValueError("count must be greater than 0")

    rng = random.Random(seed)
    if strategy == "ensemble":
        return _ensemble_tickets(history, count, rng)
    if strategy == "deep-learning":
        return _deep_learning_tickets(history, count, rng)
    if strategy == "liuyao":
        return generate_liuyao_tickets(count=count, seed=seed)[1]

    tickets: list[Ticket] = []
    while len(tickets) < count:
        if strategy == "random":
            ticket = _random_ticket(rng)
        elif strategy == "weighted":
            ticket = _weighted_ticket(history, rng)
        elif strategy == "balanced":
            ticket = _balanced_ticket(history, rng)
        elif strategy in {"hot", "cold", "omission", "recent"}:
            ticket = _score_weighted_ticket(history, rng, strategy)
        else:
            ticket = _random_ticket(rng)
        tickets.append(ticket)
    return tickets


def _random_ticket(rng: random.Random) -> Ticket:
    red = tuple(sorted(rng.sample(list(RED_RANGE), 6)))
    blue = rng.choice(list(BLUE_RANGE))
    return Ticket(red=red, blue=blue)


def _weighted_ticket(history: Sequence[Draw], rng: random.Random) -> Ticket:
    if not history:
        return _random_ticket(rng)

    analysis = analyze_draws(list(history))
    red_weights = [
        max(1, analysis.red_frequency[ball] + min(analysis.red_omissions[ball], 8))
        for ball in RED_RANGE
    ]
    blue_weights = [
        max(1, analysis.blue_frequency[ball] + min(analysis.blue_omissions[ball], 6))
        for ball in BLUE_RANGE
    ]
    red = tuple(sorted(_weighted_unique(list(RED_RANGE), red_weights, 6, rng)))
    blue = _weighted_one(list(BLUE_RANGE), blue_weights, rng)
    return Ticket(red=red, blue=blue)


def _score_weighted_ticket(history: Sequence[Draw], rng: random.Random, mode: str) -> Ticket:
    if not history:
        return _random_ticket(rng)

    ordered = sorted(history, key=lambda draw: draw.issue)
    analysis = analyze_draws(list(ordered))
    recent_draws = ordered[-min(20, len(ordered)) :]
    recent_analysis = analyze_draws(list(recent_draws))
    max_red_frequency = max(analysis.red_frequency.values()) or 1
    max_blue_frequency = max(analysis.blue_frequency.values()) or 1

    if mode == "hot":
        red_weights = [analysis.red_frequency[ball] + 1 for ball in RED_RANGE]
        blue_weights = [analysis.blue_frequency[ball] + 1 for ball in BLUE_RANGE]
    elif mode == "cold":
        red_weights = [max_red_frequency - analysis.red_frequency[ball] + 1 for ball in RED_RANGE]
        blue_weights = [max_blue_frequency - analysis.blue_frequency[ball] + 1 for ball in BLUE_RANGE]
    elif mode == "omission":
        red_weights = [min(analysis.red_omissions[ball], 12) + 1 for ball in RED_RANGE]
        blue_weights = [min(analysis.blue_omissions[ball], 8) + 1 for ball in BLUE_RANGE]
    else:
        red_weights = [recent_analysis.red_frequency[ball] * 3 + analysis.red_frequency[ball] + 1 for ball in RED_RANGE]
        blue_weights = [recent_analysis.blue_frequency[ball] * 3 + analysis.blue_frequency[ball] + 1 for ball in BLUE_RANGE]

    red = tuple(sorted(_weighted_unique(list(RED_RANGE), red_weights, 6, rng)))
    blue = _weighted_one(list(BLUE_RANGE), blue_weights, rng)
    return Ticket(red=red, blue=blue)


def _deep_learning_ticket(history: Sequence[Draw], rng: random.Random) -> Ticket:
    if not history:
        return _random_ticket(rng)
    scorer = ExperimentalNeuralScorer(history)
    return _deep_learning_ticket_from_weights(scorer.red_weights(), scorer.blue_weights(), rng)


def _deep_learning_tickets(history: Sequence[Draw], count: int, rng: random.Random) -> list[Ticket]:
    if not history:
        return [_random_ticket(rng) for _ in range(count)]
    scorer = ExperimentalNeuralScorer(history)
    red_weights = scorer.red_weights()
    blue_weights = scorer.blue_weights()
    return [_deep_learning_ticket_from_weights(red_weights, blue_weights, rng) for _ in range(count)]


def _deep_learning_ticket_from_weights(red_weights: list[float], blue_weights: list[float], rng: random.Random) -> Ticket:
    red = tuple(sorted(_weighted_unique(list(RED_RANGE), red_weights, 6, rng)))
    blue = _weighted_one(list(BLUE_RANGE), blue_weights, rng)
    return Ticket(red=red, blue=blue)


def generate_liuyao_tickets(count: int = DEFAULT_TICKET_COUNT, seed: int | None = None) -> tuple[LiuyaoReading, list[Ticket]]:
    if count < 1:
        raise ValueError("count must be greater than 0")
    rng = random.Random(seed)
    reading = cast_liuyao(rng)
    tickets = [
        Ticket(
            red=tuple(sorted(_weighted_unique(list(RED_RANGE), reading.red_weights, 6, rng))),
            blue=_weighted_one(list(BLUE_RANGE), reading.blue_weights, rng),
        )
        for _ in range(count)
    ]
    return reading, tickets


def _ensemble_tickets(history: Sequence[Draw], count: int, rng: random.Random) -> list[Ticket]:
    cycle = ["balanced", "hot", "cold", "omission", "recent"]
    tickets: list[Ticket] = []
    while len(tickets) < count:
        strategy = cycle[len(tickets) % len(cycle)]
        tickets.append(_ticket_for_strategy(history, rng, strategy))
    return tickets


def _ticket_for_strategy(history: Sequence[Draw], rng: random.Random, strategy: str) -> Ticket:
    if strategy == "balanced":
        return _balanced_ticket(history, rng)
    if strategy in {"hot", "cold", "omission", "recent"}:
        return _score_weighted_ticket(history, rng, strategy)
    if strategy == "weighted":
        return _weighted_ticket(history, rng)
    return _random_ticket(rng)


def _balanced_ticket(history: Sequence[Draw], rng: random.Random) -> Ticket:
    for _ in range(200):
        ticket = _weighted_ticket(history, rng) if history else _random_ticket(rng)
        if _is_balanced(ticket):
            return ticket
    return _random_ticket(rng)


def _weighted_unique(items: list[int], weights: Sequence[float], count: int, rng: random.Random) -> list[int]:
    selected: list[int] = []
    available_items = list(items)
    available_weights = list(weights)
    while len(selected) < count:
        choice = _weighted_one(available_items, available_weights, rng)
        index = available_items.index(choice)
        selected.append(choice)
        del available_items[index]
        del available_weights[index]
    return selected


def _weighted_one(items: list[int], weights: Sequence[float], rng: random.Random) -> int:
    total = sum(weights)
    pick = rng.uniform(0, total)
    current = 0.0
    for item, weight in zip(items, weights):
        current += weight
        if pick <= current:
            return item
    return items[-1]


def _is_balanced(ticket: Ticket) -> bool:
    odd = sum(1 for ball in ticket.red if ball % 2)
    low = sum(1 for ball in ticket.red if 1 <= ball <= 11)
    mid = sum(1 for ball in ticket.red if 12 <= ball <= 22)
    high = sum(1 for ball in ticket.red if 23 <= ball <= 33)
    consecutive_pairs = sum(1 for left, right in zip(ticket.red, ticket.red[1:]) if right == left + 1)

    return 2 <= odd <= 4 and max(low, mid, high) <= 4 and consecutive_pairs <= 2
