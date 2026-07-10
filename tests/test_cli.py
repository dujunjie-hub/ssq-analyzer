from datetime import date

import pytest

import ssq_analyzer.cli as cli
from ssq_analyzer.cli import main
from ssq_analyzer.data import DataFetchError
from ssq_analyzer.models import Draw


@pytest.fixture(autouse=True)
def use_small_history(monkeypatch):
    draws = [
        Draw("2026001", date(2026, 1, 1), (1, 2, 3, 4, 5, 6), 1),
        Draw("2026002", date(2026, 1, 3), (7, 8, 9, 10, 11, 12), 2),
        Draw("2026003", date(2026, 1, 5), (13, 14, 15, 16, 17, 18), 3),
        Draw("2026004", date(2026, 1, 7), (19, 20, 21, 22, 23, 24), 4),
    ]
    monkeypatch.setattr(cli, "load_draws", lambda: draws)


def test_generate_command_outputs_five_tickets(capsys):
    exit_code = main(["generate", "--seed", "9"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "娱乐参考" in output
    assert "下期开奖预计" in output
    assert output.count("红球") == 5


def test_analyze_command_exports_csv(tmp_path):
    output = tmp_path / "analysis.csv"

    exit_code = main(["analyze", "--format", "csv", "--output", str(output)])

    assert exit_code == 0
    assert output.exists()


def test_generate_accepts_ensemble_strategy(capsys):
    exit_code = main(["generate", "--strategy", "ensemble", "--seed", "9"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert output.count("红球") == 5


def test_generate_deep_learning_prints_experimental_warning(capsys):
    exit_code = main(["generate", "--strategy", "deep-learning", "--seed", "9"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "实验策略" in output


def test_compare_command_exports_strategy_summary(tmp_path):
    output = tmp_path / "compare.csv"

    exit_code = main(["compare", "--seed", "9", "--format", "csv", "--output", str(output)])

    assert exit_code == 0
    assert output.exists()
    exported = output.read_text(encoding="utf-8")
    assert "strategy" in exported
    assert "liuyao" in exported


def test_generate_liuyao_prints_and_exports_reading_metadata(capsys, tmp_path):
    output_path = tmp_path / "liuyao.csv"

    exit_code = main(
        [
            "generate",
            "--strategy",
            "liuyao",
            "--seed",
            "9",
            "--format",
            "csv",
            "--output",
            str(output_path),
        ]
    )

    output = capsys.readouterr().out
    exported = output_path.read_text(encoding="utf-8")
    assert exit_code == 0
    assert "六爻灵感娱乐策略" in output
    assert "本卦：" in output
    assert "动爻：" in output
    assert "变卦：" in output
    assert output.count("红球") == 5
    assert "primary_hexagram" in exported
    assert "changed_hexagram" in exported


def test_generate_advanced_liuyao_prints_traditional_context(capsys):
    exit_code = main(["generate", "--strategy", "liuyao-advanced", "--seed", "19930810", "--count", "1"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "世应：" in output
    assert "用神：妻财" in output
    assert "纳甲六亲：" in output
    assert output.count("红球") == 1


def test_fetch_network_failure_returns_friendly_error_without_traceback(monkeypatch, capsys):
    def fail_fetch():
        raise DataFetchError("无法访问开奖数据源：DNS 解析失败")

    monkeypatch.setattr(cli, "fetch_draws", fail_fetch)

    exit_code = main(["fetch"])

    output = capsys.readouterr().err
    assert exit_code == 1
    assert "历史数据更新失败" in output
    assert "DNS 解析失败" in output
    assert "Traceback" not in output
