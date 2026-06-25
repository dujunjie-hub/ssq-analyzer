from datetime import date

from ssq_analyzer.backtest import compare_strategies, prize_tier, run_backtest, summarize_backtest
from ssq_analyzer.exporters import export_rows
from ssq_analyzer.models import Draw


def draws():
    return [
        Draw("2026001", date(2026, 1, 1), (1, 2, 3, 4, 5, 6), 1),
        Draw("2026002", date(2026, 1, 3), (7, 8, 9, 10, 11, 12), 2),
        Draw("2026003", date(2026, 1, 5), (13, 14, 15, 16, 17, 18), 3),
    ]


def test_prize_tier_rules():
    assert prize_tier(red_hits=6, blue_hit=True) == "first"
    assert prize_tier(red_hits=6, blue_hit=False) == "second"
    assert prize_tier(red_hits=0, blue_hit=True) == "sixth"
    assert prize_tier(red_hits=2, blue_hit=False) == "none"


def test_backtest_uses_only_prior_draws():
    results = run_backtest(draws(), strategy="random", count=2, seed=5, window=2)

    assert [result.issue for result in results] == ["2026002", "2026003"]
    assert all(result.training_draw_count < 3 for result in results)
    assert all(len(result.generated_tickets) == 2 for result in results)


def test_export_rows_creates_csv_and_xlsx(tmp_path):
    rows = [{"issue": "2026001", "red_hits": 3, "tier": "none"}]

    csv_path = export_rows(rows, tmp_path / "result.csv")
    xlsx_path = export_rows(rows, tmp_path / "result.xlsx")

    assert csv_path.exists()
    assert xlsx_path.exists()
    assert csv_path.read_text(encoding="utf-8").startswith("issue,red_hits,tier")


def test_summarize_backtest_reports_distribution_and_blue_rate():
    results = run_backtest(draws(), strategy="random", count=2, seed=5, window=2)

    summary = summarize_backtest(results, strategy="random")

    assert summary["strategy"] == "random"
    assert summary["total_tickets"] == 4
    assert "blue_hit_rate" in summary
    assert "tier_none" in summary
    assert "red_hits_0" in summary


def test_compare_strategies_returns_one_summary_per_strategy():
    summaries = compare_strategies(draws(), strategies=["random", "balanced"], count=2, seed=5, window=2)

    assert [summary["strategy"] for summary in summaries] == ["random", "balanced"]
    assert all(summary["total_tickets"] == 4 for summary in summaries)
