from app.scripts.registry import create_default_registry
from ssq_analyzer.budget import calculate_budget_plan


def test_compound_budget_plan_maximizes_valid_coverage_within_budget():
    plan = calculate_budget_plan(mode="compound", budget=100)

    assert plan.combination_count == 49
    assert plan.cost == 98
    assert plan.remaining_budget == 2
    assert plan.red_count == 7
    assert plan.blue_count == 7
    assert plan.first_prize_denominator == 17_721_088


def test_dantuo_budget_plan_uses_selected_red_dan_count():
    plan = calculate_budget_plan(mode="dantuo", budget=100, red_dan_count=1)

    assert plan.combination_count == 48
    assert plan.cost == 96
    assert plan.red_dan_count == 1
    assert plan.red_tuo_count == 6
    assert plan.blue_count == 8


def test_budget_tool_is_available_from_the_gui_registry():
    result = create_default_registry().run("ssq_budget", {"mode": "compound", "budget": 100, "red_dan_count": 1})

    assert result.rows[0]["覆盖组合数（注）"] == 49
    assert "一等奖理论概率" in result.summary_text
