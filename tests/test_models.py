from datetime import date

import pytest

from ssq_analyzer.models import Draw, Ticket


def test_ticket_requires_six_unique_sorted_red_balls():
    ticket = Ticket(red=(1, 5, 9, 12, 18, 33), blue=16)

    assert ticket.red == (1, 5, 9, 12, 18, 33)
    assert ticket.blue == 16


def test_ticket_rejects_duplicate_red_balls():
    with pytest.raises(ValueError, match="six unique"):
        Ticket(red=(1, 1, 9, 12, 18, 33), blue=16)


def test_draw_validates_date_issue_and_values():
    draw = Draw(
        issue="2026001",
        draw_date=date(2026, 1, 1),
        red=(2, 4, 6, 8, 10, 12),
        blue=3,
    )

    assert draw.issue == "2026001"
    assert draw.ticket == Ticket(red=(2, 4, 6, 8, 10, 12), blue=3)
