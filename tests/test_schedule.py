from datetime import date, datetime
from zoneinfo import ZoneInfo

from ssq_analyzer.schedule import format_next_draw_time, history_staleness_warning, latest_completed_draw_date, next_draw_time


def test_next_draw_time_uses_same_draw_day_before_draw_time():
    now = datetime(2026, 6, 16, 20, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    result = next_draw_time(now)

    assert result == datetime(2026, 6, 16, 21, 15, tzinfo=ZoneInfo("Asia/Shanghai"))


def test_next_draw_time_moves_to_next_draw_day_after_draw_time():
    now = datetime(2026, 6, 16, 22, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    result = next_draw_time(now)

    assert result == datetime(2026, 6, 18, 21, 15, tzinfo=ZoneInfo("Asia/Shanghai"))


def test_format_next_draw_time_includes_beijing_time_and_schedule_note():
    now = datetime(2026, 6, 12, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    text = format_next_draw_time(now)

    assert "下期开奖预计：" in text
    assert "2026-06-14 周日 21:15" in text
    assert "北京时间" in text


def test_latest_completed_draw_date_uses_previous_draw_after_draw_time():
    now = datetime(2026, 7, 13, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    assert latest_completed_draw_date(now) == date(2026, 7, 12)


def test_history_staleness_warning_reports_missing_latest_draw():
    now = datetime(2026, 7, 13, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    warning = history_staleness_warning(date(2026, 7, 9), now)

    assert "开奖数据可能未更新" in warning
    assert "2026-07-09" in warning
    assert "2026-07-12" in warning
