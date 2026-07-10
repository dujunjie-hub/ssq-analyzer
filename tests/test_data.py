import urllib.error

import pytest

from ssq_analyzer import data
from ssq_analyzer.data import DataFetchError, fetch_draws, parse_500_history_html


def test_parse_500_history_html_sorts_red_balls_before_validation():
    html = """
    <table>
      <tr>
        <td>2026071</td>
        <td>12</td><td>03</td><td>09</td><td>01</td><td>33</td><td>18</td><td>07</td>
        <td></td><td></td><td></td><td></td><td></td><td></td><td></td>
        <td>2026-06-14</td>
      </tr>
    </table>
    """

    draws = parse_500_history_html(html)

    assert len(draws) == 1
    assert draws[0].red == (1, 3, 9, 12, 18, 33)
    assert draws[0].blue == 7


def test_parse_500_history_html_handles_real_500_shifted_columns():
    html = """
    <table>
      <tr>
        <td>2</td><td>26066</td>
        <td>05</td><td>11</td><td>21</td><td>23</td><td>24</td><td>29</td><td>16</td>
        <td>&nbsp;</td><td>671,837,950</td><td>7</td><td>6,728,458</td>
        <td>126</td><td>384,101</td><td>392,786,646</td><td>2026-06-11</td>
      </tr>
    </table>
    """

    draws = parse_500_history_html(html)

    assert len(draws) == 1
    assert draws[0].issue == "26066"
    assert draws[0].red == (5, 11, 21, 23, 24, 29)
    assert draws[0].blue == 16


def test_fetch_draws_wraps_dns_failure_in_friendly_error(monkeypatch):
    def fail_urlopen(*args, **kwargs):
        raise urllib.error.URLError("dns lookup failed")

    monkeypatch.setattr("ssq_analyzer.data.urllib.request.urlopen", fail_urlopen)

    with pytest.raises(DataFetchError, match="无法访问开奖数据源"):
        fetch_draws()


def test_default_history_path_finds_repo_data_from_packaged_app(monkeypatch, tmp_path):
    history = tmp_path / "data" / "ssq_history.csv"
    history.parent.mkdir()
    history.write_text("issue,date,red_1,red_2,red_3,red_4,red_5,red_6,blue\n", encoding="utf-8")
    app_exe = tmp_path / "dist" / "SSQ Analyzer.app" / "Contents" / "MacOS" / "SSQ Analyzer"
    app_exe.parent.mkdir(parents=True)
    app_exe.write_text("", encoding="utf-8")

    monkeypatch.delenv("SSQ_HISTORY_PATH", raising=False)
    monkeypatch.setattr(data.sys, "executable", str(app_exe))

    assert data._default_history_path() == history
