from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


BEIJING_TZ = ZoneInfo("Asia/Shanghai")
DRAW_WEEKDAYS = {1: "周二", 3: "周四", 6: "周日"}
DRAW_TIME = time(21, 15)


def next_draw_time(now: datetime | None = None) -> datetime:
    current = now or datetime.now(BEIJING_TZ)
    if current.tzinfo is None:
        current = current.replace(tzinfo=BEIJING_TZ)
    current = current.astimezone(BEIJING_TZ)

    for days_ahead in range(8):
        candidate_date = current.date() + timedelta(days=days_ahead)
        if candidate_date.weekday() not in DRAW_WEEKDAYS:
            continue
        candidate = datetime.combine(candidate_date, DRAW_TIME, tzinfo=BEIJING_TZ)
        if candidate > current:
            return candidate
    raise RuntimeError("unable to calculate next draw time")


def format_next_draw_time(now: datetime | None = None) -> str:
    draw_at = next_draw_time(now)
    weekday = DRAW_WEEKDAYS[draw_at.weekday()]
    return (
        f"下期开奖预计：{draw_at:%Y-%m-%d} {weekday} {draw_at:%H:%M}"
        "（北京时间，按周二/周四/周日开奖规则估算）"
    )


def latest_completed_draw_date(now: datetime | None = None) -> date | None:
    current = now or datetime.now(BEIJING_TZ)
    if current.tzinfo is None:
        current = current.replace(tzinfo=BEIJING_TZ)
    current = current.astimezone(BEIJING_TZ)

    for days_back in range(8):
        candidate_date = current.date() - timedelta(days=days_back)
        if candidate_date.weekday() not in DRAW_WEEKDAYS:
            continue
        candidate = datetime.combine(candidate_date, DRAW_TIME, tzinfo=BEIJING_TZ)
        if candidate <= current:
            return candidate_date
    return None


def history_staleness_warning(latest_draw_date: date, now: datetime | None = None) -> str:
    expected_date = latest_completed_draw_date(now)
    if expected_date is None or latest_draw_date >= expected_date:
        return ""
    return (
        f"开奖数据可能未更新：本地最新开奖日期为 {latest_draw_date.isoformat()}，"
        f"按开奖规则预计应已有 {expected_date.isoformat()} 的开奖数据。请先点击“刷新历史数据”。"
    )
