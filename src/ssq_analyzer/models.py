from __future__ import annotations

from dataclasses import dataclass
from datetime import date


RED_RANGE = range(1, 34)
BLUE_RANGE = range(1, 17)


@dataclass(frozen=True)
class Ticket:
    red: tuple[int, ...]
    blue: int

    def __post_init__(self) -> None:
        red = tuple(self.red)
        if len(red) != 6 or len(set(red)) != 6:
            raise ValueError("ticket must contain six unique red balls")
        if red != tuple(sorted(red)):
            raise ValueError("red balls must be sorted")
        if any(ball not in RED_RANGE for ball in red):
            raise ValueError("red balls must be between 1 and 33")
        if self.blue not in BLUE_RANGE:
            raise ValueError("blue ball must be between 1 and 16")

        object.__setattr__(self, "red", red)

    def red_text(self) -> str:
        return " ".join(f"{ball:02d}" for ball in self.red)

    def blue_text(self) -> str:
        return f"{self.blue:02d}"


@dataclass(frozen=True)
class Draw:
    issue: str
    draw_date: date
    red: tuple[int, ...]
    blue: int

    def __post_init__(self) -> None:
        if not str(self.issue).strip():
            raise ValueError("issue is required")
        if not isinstance(self.draw_date, date):
            raise ValueError("draw_date must be a date")
        ticket = Ticket(self.red, self.blue)
        object.__setattr__(self, "issue", str(self.issue).strip())
        object.__setattr__(self, "red", ticket.red)

    @property
    def ticket(self) -> Ticket:
        return Ticket(red=self.red, blue=self.blue)
