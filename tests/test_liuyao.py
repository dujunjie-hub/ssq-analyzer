import random

from ssq_analyzer.generator import generate_liuyao_tickets
from ssq_analyzer.liuyao import cast_liuyao, reading_from_lines


def test_cast_liuyao_is_reproducible_with_fixed_seed():
    first = cast_liuyao(random.Random(9))
    second = cast_liuyao(random.Random(9))

    assert first == second
    assert len(first.line_values) == 6
    assert set(first.line_values) <= {6, 7, 8, 9}
    assert first.primary_hexagram
    assert first.changed_hexagram


def test_reading_identifies_moving_lines_and_changes_hexagram():
    reading = reading_from_lines((6, 7, 8, 9, 7, 8))

    assert reading.moving_lines == (1, 4)
    assert reading.moving_lines_text == "初爻、四爻"
    assert reading.primary_hexagram != reading.changed_hexagram


def test_reading_produces_positive_ball_weights():
    reading = reading_from_lines((6, 7, 8, 9, 7, 8))

    assert len(reading.red_weights) == 33
    assert len(reading.blue_weights) == 16
    assert all(weight > 0 for weight in reading.red_weights)
    assert all(weight > 0 for weight in reading.blue_weights)


def test_generate_liuyao_tickets_reuses_one_reading_for_five_legal_tickets():
    first_reading, first_tickets = generate_liuyao_tickets(count=5, seed=9)
    second_reading, second_tickets = generate_liuyao_tickets(count=5, seed=9)

    assert first_reading == second_reading
    assert first_tickets == second_tickets
    assert len(first_tickets) == 5
    assert all(len(ticket.red) == 6 for ticket in first_tickets)
    assert all(ticket.red == tuple(sorted(ticket.red)) for ticket in first_tickets)
