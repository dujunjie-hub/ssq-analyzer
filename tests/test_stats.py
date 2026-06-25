from datetime import date

from ssq_analyzer.models import Draw
from ssq_analyzer.stats import analyze_draws, red_omissions


def sample_draws():
    return [
        Draw("2026001", date(2026, 1, 1), (1, 2, 3, 4, 5, 6), 1),
        Draw("2026002", date(2026, 1, 3), (1, 7, 8, 9, 10, 11), 2),
        Draw("2026003", date(2026, 1, 5), (12, 13, 14, 15, 16, 17), 1),
    ]


def test_analyze_draws_counts_frequency_and_shape():
    result = analyze_draws(sample_draws())

    assert result.red_frequency[1] == 2
    assert result.blue_frequency[1] == 2
    assert result.parity_counts["3:3"] == 2
    assert result.range_counts["low_mid_high"]["6:0:0"] == 2


def test_red_omissions_count_draws_since_last_seen():
    omissions = red_omissions(sample_draws())

    assert omissions[1] == 1
    assert omissions[18] == 3
