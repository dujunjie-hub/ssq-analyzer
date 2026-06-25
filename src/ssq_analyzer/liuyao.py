from __future__ import annotations

import random
from dataclasses import dataclass


LINE_NAMES = ("初爻", "二爻", "三爻", "四爻", "五爻", "上爻")

TRIGRAMS = {
    (1, 1, 1): "乾",
    (1, 1, 0): "兑",
    (1, 0, 1): "离",
    (1, 0, 0): "震",
    (0, 1, 1): "巽",
    (0, 1, 0): "坎",
    (0, 0, 1): "艮",
    (0, 0, 0): "坤",
}

HEXAGRAMS = {
    ("乾", "乾"): (1, "乾为天"),
    ("坤", "坤"): (2, "坤为地"),
    ("坎", "震"): (3, "水雷屯"),
    ("艮", "坎"): (4, "山水蒙"),
    ("坎", "乾"): (5, "水天需"),
    ("乾", "坎"): (6, "天水讼"),
    ("坤", "坎"): (7, "地水师"),
    ("坎", "坤"): (8, "水地比"),
    ("巽", "乾"): (9, "风天小畜"),
    ("乾", "兑"): (10, "天泽履"),
    ("坤", "乾"): (11, "地天泰"),
    ("乾", "坤"): (12, "天地否"),
    ("乾", "离"): (13, "天火同人"),
    ("离", "乾"): (14, "火天大有"),
    ("坤", "艮"): (15, "地山谦"),
    ("震", "坤"): (16, "雷地豫"),
    ("兑", "震"): (17, "泽雷随"),
    ("艮", "巽"): (18, "山风蛊"),
    ("坤", "兑"): (19, "地泽临"),
    ("巽", "坤"): (20, "风地观"),
    ("离", "震"): (21, "火雷噬嗑"),
    ("艮", "离"): (22, "山火贲"),
    ("艮", "坤"): (23, "山地剥"),
    ("坤", "震"): (24, "地雷复"),
    ("乾", "震"): (25, "天雷无妄"),
    ("艮", "乾"): (26, "山天大畜"),
    ("艮", "震"): (27, "山雷颐"),
    ("兑", "巽"): (28, "泽风大过"),
    ("坎", "坎"): (29, "坎为水"),
    ("离", "离"): (30, "离为火"),
    ("兑", "艮"): (31, "泽山咸"),
    ("震", "巽"): (32, "雷风恒"),
    ("乾", "艮"): (33, "天山遁"),
    ("震", "乾"): (34, "雷天大壮"),
    ("离", "坤"): (35, "火地晋"),
    ("坤", "离"): (36, "地火明夷"),
    ("巽", "离"): (37, "风火家人"),
    ("离", "兑"): (38, "火泽睽"),
    ("坎", "艮"): (39, "水山蹇"),
    ("震", "坎"): (40, "雷水解"),
    ("艮", "兑"): (41, "山泽损"),
    ("巽", "震"): (42, "风雷益"),
    ("兑", "乾"): (43, "泽天夬"),
    ("乾", "巽"): (44, "天风姤"),
    ("兑", "坤"): (45, "泽地萃"),
    ("坤", "巽"): (46, "地风升"),
    ("兑", "坎"): (47, "泽水困"),
    ("坎", "巽"): (48, "水风井"),
    ("兑", "离"): (49, "泽火革"),
    ("离", "巽"): (50, "火风鼎"),
    ("震", "震"): (51, "震为雷"),
    ("艮", "艮"): (52, "艮为山"),
    ("巽", "艮"): (53, "风山渐"),
    ("震", "兑"): (54, "雷泽归妹"),
    ("震", "离"): (55, "雷火丰"),
    ("离", "艮"): (56, "火山旅"),
    ("巽", "巽"): (57, "巽为风"),
    ("兑", "兑"): (58, "兑为泽"),
    ("巽", "坎"): (59, "风水涣"),
    ("坎", "兑"): (60, "水泽节"),
    ("巽", "兑"): (61, "风泽中孚"),
    ("震", "艮"): (62, "雷山小过"),
    ("坎", "离"): (63, "水火既济"),
    ("离", "坎"): (64, "火水未济"),
}


@dataclass(frozen=True)
class LiuyaoReading:
    line_values: tuple[int, ...]
    moving_lines: tuple[int, ...]
    primary_number: int
    primary_hexagram: str
    changed_number: int
    changed_hexagram: str
    red_weights: tuple[float, ...]
    blue_weights: tuple[float, ...]

    @property
    def moving_lines_text(self) -> str:
        if not self.moving_lines:
            return "无动爻"
        return "、".join(LINE_NAMES[position - 1] for position in self.moving_lines)

    @property
    def line_values_text(self) -> str:
        return "-".join(str(value) for value in self.line_values)


def cast_liuyao(rng: random.Random) -> LiuyaoReading:
    return reading_from_lines(tuple(rng.choice((6, 7, 8, 9)) for _ in range(6)))


def reading_from_lines(line_values: tuple[int, ...]) -> LiuyaoReading:
    if len(line_values) != 6 or any(value not in {6, 7, 8, 9} for value in line_values):
        raise ValueError("liuyao reading requires six line values from 6, 7, 8, and 9")

    primary_bits = tuple(value % 2 for value in line_values)
    changed_bits = tuple(_changed_bit(value) for value in line_values)
    moving_lines = tuple(index for index, value in enumerate(line_values, start=1) if value in {6, 9})
    primary_number, primary_hexagram = _resolve_hexagram(primary_bits)
    changed_number, changed_hexagram = _resolve_hexagram(changed_bits)
    red_weights = _ball_weights(33, line_values, primary_number, changed_number, moving_lines)
    blue_weights = _ball_weights(16, tuple(reversed(line_values)), changed_number, primary_number, moving_lines)

    return LiuyaoReading(
        line_values=line_values,
        moving_lines=moving_lines,
        primary_number=primary_number,
        primary_hexagram=primary_hexagram,
        changed_number=changed_number,
        changed_hexagram=changed_hexagram,
        red_weights=red_weights,
        blue_weights=blue_weights,
    )


def _changed_bit(value: int) -> int:
    if value == 6:
        return 1
    if value == 9:
        return 0
    return value % 2


def _resolve_hexagram(bits: tuple[int, ...]) -> tuple[int, str]:
    lower = TRIGRAMS[bits[:3]]
    upper = TRIGRAMS[bits[3:]]
    return HEXAGRAMS[(upper, lower)]


def _ball_weights(
    maximum: int,
    line_values: tuple[int, ...],
    primary_number: int,
    changed_number: int,
    moving_lines: tuple[int, ...],
) -> tuple[float, ...]:
    anchors = [
        ((value * position + primary_number + changed_number + sum(moving_lines)) % maximum) + 1
        for position, value in enumerate(line_values, start=1)
    ]
    weights: list[float] = []
    for ball in range(1, maximum + 1):
        weight = 1.0
        for position, anchor in enumerate(anchors, start=1):
            distance = abs(ball - anchor)
            distance = min(distance, maximum - distance)
            influence = 7.0 if position in moving_lines else 4.0
            weight += influence / (1 + distance)
        if ball % 2 == primary_number % 2:
            weight += 0.75
        weights.append(weight)
    return tuple(weights)
