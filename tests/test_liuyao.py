import random

from ssq_analyzer.generator import generate_advanced_liuyao_tickets, generate_tickets
from ssq_analyzer.liuyao import cast_liuyao, line_values_from_input, reading_from_lines


def test_cast_liuyao_is_reproducible_with_fixed_seed():
    first = cast_liuyao(random.Random(9))
    second = cast_liuyao(random.Random(9))

    assert first == second
    assert len(first.line_values) == 6
    assert set(first.line_values) <= {6, 7, 8, 9}
    assert first.primary_hexagram
    assert first.changed_hexagram


def test_input_cast_is_stable_and_preserves_valid_line_values():
    first_lines = line_values_from_input("徐 19930810")
    second_lines = line_values_from_input("徐 19930810")

    assert first_lines == second_lines
    assert len(first_lines) == 6
    assert set(first_lines) <= {6, 7, 8, 9}


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
    from ssq_analyzer.generator import generate_liuyao_tickets

    first_reading, first_tickets = generate_liuyao_tickets(count=5, seed=9)
    second_reading, second_tickets = generate_liuyao_tickets(count=5, seed=9)

    assert first_reading == second_reading
    assert first_tickets == second_tickets
    assert len(first_tickets) == 5
    assert all(len(ticket.red) == 6 for ticket in first_tickets)
    assert all(ticket.red == tuple(sorted(ticket.red)) for ticket in first_tickets)


def test_generate_liuyao_tickets_uses_cast_input_with_a_fixed_seed():
    from ssq_analyzer.generator import generate_liuyao_tickets

    first_reading, first_tickets = generate_liuyao_tickets(count=3, seed=9, cast_input="徐 19930810")
    second_reading, second_tickets = generate_liuyao_tickets(count=3, seed=9, cast_input="徐 19930810")

    assert first_reading.line_values == line_values_from_input("徐 19930810")
    assert first_reading == second_reading
    assert first_tickets == second_tickets


def test_advanced_liuyao_adds_traditional_context_and_legal_tickets():
    reading, tickets = generate_advanced_liuyao_tickets(count=3, seed=19930810)

    assert len(reading.najia_lines) == 6
    assert len(reading.six_relatives) == 6
    assert reading.world_line in range(1, 7)
    assert reading.responding_line in range(1, 7)
    assert reading.use_god == "妻财"
    assert reading.hidden_hexagram
    assert reading.opposite_hexagram
    assert len(tickets) == 3
    assert all(len(ticket.red) == 6 for ticket in tickets)


def test_generate_tickets_supports_advanced_liuyao_strategy():
    tickets = generate_tickets([], strategy="liuyao-advanced", count=1, seed=19930810)

    assert len(tickets) == 1
    assert len(tickets[0].red) == 6
