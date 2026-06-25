from __future__ import annotations

import math
from collections.abc import Sequence

from ssq_analyzer.models import BLUE_RANGE, RED_RANGE, Draw


class ExperimentalNeuralScorer:
    """Tiny deterministic neural-style scorer for entertainment-only sampling."""

    def __init__(self, history: Sequence[Draw], hidden_size: int = 8) -> None:
        self.history = sorted(history, key=lambda draw: draw.issue)
        self.hidden_size = hidden_size

    def red_weights(self) -> list[float]:
        return self._weights(list(RED_RANGE), "red")

    def blue_weights(self) -> list[float]:
        return self._weights(list(BLUE_RANGE), "blue")

    def _weights(self, balls: list[int], color: str) -> list[float]:
        if not self.history:
            return [1.0 for _ in balls]

        draw_vectors = [self._draw_vector(draw) for draw in self.history]
        recency_total = max(1, len(draw_vectors) - 1)
        weights: list[float] = []
        for ball in balls:
            score = 0.0
            for draw_index, vector in enumerate(draw_vectors):
                recency = 1.0 + draw_index / recency_total
                hidden = self._hidden_activation(vector, ball, color)
                appeared = self._appeared(self.history[draw_index], ball, color)
                score += recency * hidden * (1.25 if appeared else 0.85)
            weights.append(max(0.1, math.exp(score / len(draw_vectors))))
        return weights

    def _draw_vector(self, draw: Draw) -> list[float]:
        red_sum = sum(draw.red) / (33 * 6)
        red_odd = sum(1 for ball in draw.red if ball % 2) / 6
        low = sum(1 for ball in draw.red if ball <= 11) / 6
        mid = sum(1 for ball in draw.red if 12 <= ball <= 22) / 6
        high = sum(1 for ball in draw.red if ball >= 23) / 6
        blue = draw.blue / 16
        return [red_sum, red_odd, low, mid, high, blue]

    def _hidden_activation(self, vector: list[float], ball: int, color: str) -> float:
        normalized_ball = ball / (33 if color == "red" else 16)
        total = 0.0
        for hidden_index in range(self.hidden_size):
            bias = math.sin((hidden_index + 1) * normalized_ball)
            weighted = sum(
                value * math.cos((hidden_index + 1) * (feature_index + 1) * normalized_ball)
                for feature_index, value in enumerate(vector)
            )
            total += math.tanh(weighted + bias)
        return (total / self.hidden_size + 1.2) / 2.4

    def _appeared(self, draw: Draw, ball: int, color: str) -> bool:
        if color == "red":
            return ball in draw.red
        return ball == draw.blue
