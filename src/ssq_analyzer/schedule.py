from __future__ import annotations

from datetime import datetime, time, timedelta
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
