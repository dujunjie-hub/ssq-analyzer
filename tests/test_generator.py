from datetime import date

from ssq_analyzer.generator import generate_tickets
from ssq_analyzer.deep_learning import ExperimentalNeuralScorer
from ssq_analyzer.models import Draw


def history():
    return [
        Draw("2026001", date(2026, 1, 1), (1, 2, 3, 4, 5, 6), 1),
        Draw("2026002", date(2026, 1, 3), (7, 8, 9, 10, 11, 12), 2),
        Draw("2026003", date(2026, 1, 5), (13, 14, 15, 16, 17, 18), 3),
    ]


def test_generate_defaults_to_five_legal_tickets():
    tickets = generate_tickets(history(), strategy="random", seed=7)

    assert len(tickets) == 5
    assert all(len(ticket.red) == 6 for ticket in tickets)
    assert all(ticket.red == tuple(sorted(ticket.red)) for ticket in tickets)


def test_generation_is_deterministic_with_seed():
    first = generate_tickets(history(), strategy="balanced", seed=42)
    second = generate_tickets(history(), strategy="balanced", seed=42)

    assert first == second


def test_weighted_strategy_returns_requested_count():
    tickets = generate_tickets(history(), strategy="weighted", count=3, seed=11)

    assert len(tickets) == 3


def test_transparent_strategies_generate_five_legal_tickets_by_default():
    for strategy in ["hot", "cold", "omission", "recent", "ensemble"]:
        tickets = generate_tickets(history(), strategy=strategy, seed=17)

        assert len(tickets) == 5
        assert all(len(ticket.red) == 6 for ticket in tickets)
        assert all(ticket.red == tuple(sorted(ticket.red)) for ticket in tickets)
        assert all(1 <= ticket.blue <= 16 for ticket in tickets)


def test_experimental_deep_learning_strategy_is_deterministic_and_legal():
    scorer = ExperimentalNeuralScorer(history())

    assert scorer.red_weights()[0] > 0

    first = generate_tickets(history(), strategy="deep-learning", seed=23)
    second = generate_tickets(history(), strategy="deep-learning", seed=23)

    assert first == second
    assert len(first) == 5
    assert all(len(ticket.red) == 6 for ticket in first)
    assert all(ticket.red == tuple(sorted(ticket.red)) for ticket in first)


def test_deep_learning_strategy_reuses_one_scorer_for_multiple_tickets(monkeypatch):
    calls = {"count": 0}

    class CountingScorer(ExperimentalNeuralScorer):
        def __init__(self, draws):
            calls["count"] += 1
            super().__init__(draws)

    monkeypatch.setattr("ssq_analyzer.generator.ExperimentalNeuralScorer", CountingScorer)

    generate_tickets(history(), strategy="deep-learning", count=5, seed=23)

    assert calls["count"] == 1
