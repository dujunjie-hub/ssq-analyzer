from datetime import datetime
from zoneinfo import ZoneInfo

from ssq_analyzer.schedule import format_next_draw_time, next_draw_time


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
